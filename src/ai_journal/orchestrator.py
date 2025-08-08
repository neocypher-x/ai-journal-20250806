"""
Main orchestrator for coordinating agent calls and response composition.
"""

import asyncio
import uuid
import time
import logging
from typing import List

from .models import ReflectRequest, ReflectResponse, ProcessingContext, AgentCallResult
from .agents import JournalIngestorAgent, BuddhistCoachAgent, StoicCoachAgent, ExistentialistCoachAgent
from .composer import ResponseComposer
from .config import settings, validate_settings
from .logging_config import log_request_metrics, create_trace_logger


class ReflectionOrchestrator:
    """Main orchestrator for the reflection system."""
    
    def __init__(self):
        validate_settings()
        
        self.ingestor = JournalIngestorAgent()
        self.coaches = [
            BuddhistCoachAgent(),
            StoicCoachAgent(), 
            ExistentialistCoachAgent()
        ]
        self.composer = ResponseComposer()
        self.logger = logging.getLogger("ai_journal.orchestrator")
    
    async def process_reflection(self, request: ReflectRequest) -> ReflectResponse:
        """Main entry point for processing reflection requests."""
        
        # Create processing context
        trace_id = str(uuid.uuid4())
        context = ProcessingContext(
            trace_id=trace_id,
            request=request
        )
        
        trace_logger = create_trace_logger(trace_id)
        trace_logger.info(f"Starting reflection processing for {len(request.journal_text)} chars")
        
        start_time = time.time()
        
        try:
            # Apply global timeout to entire request
            response = await asyncio.wait_for(
                self._process_with_steps(context, trace_logger),
                timeout=settings.GLOBAL_TIMEOUT_SEC
            )
            
            # Log success metrics
            total_duration = int((time.time() - start_time) * 1000)
            successful_agents = sum(1 for r in context.agent_results if r.success)
            
            log_request_metrics(
                trace_id=trace_id,
                total_duration_ms=total_duration,
                agent_count=successful_agents,
                prompts_generated=len(response.prompts)
            )
            
            trace_logger.info(f"Successfully processed reflection in {total_duration}ms")
            return response
            
        except asyncio.TimeoutError:
            total_duration = int((time.time() - start_time) * 1000)
            trace_logger.error(f"Global timeout after {total_duration}ms")
            raise
        
        except Exception as e:
            total_duration = int((time.time() - start_time) * 1000)
            trace_logger.error(f"Processing failed after {total_duration}ms: {str(e)}")
            raise
    
    async def _process_with_steps(self, context: ProcessingContext, 
                                 trace_logger) -> ReflectResponse:
        """Process the request through all steps."""
        
        # Step 1: Ingest journal
        trace_logger.info("Step 1: Ingesting journal")
        await self._ingest_journal(context, trace_logger)
        
        if not context.ingest_result:
            raise ValueError("Journal ingestion failed")
        
        # Step 2: Call philosophy coaches in parallel
        trace_logger.info("Step 2: Calling philosophy coaches")
        await self._call_coaches(context, trace_logger)
        
        # Check if we have any successful coach results
        successful_coaches = [r for r in context.agent_results if r.success]
        if not successful_coaches:
            context.warnings.append("All philosophy coaches failed - response may be limited")
            trace_logger.warning("No successful coach results")
        
        # Step 3: Compose final response
        trace_logger.info("Step 3: Composing response")
        response = self.composer.compose(context)
        
        return response
    
    async def _ingest_journal(self, context: ProcessingContext, trace_logger):
        """Handle journal ingestion step."""
        
        try:
            result = await self.ingestor.call_with_timeout(
                journal_text=context.request.journal_text,
                trace_id=context.trace_id
            )
            
            if result.success:
                # Parse the IngestResult from the agent result
                from .models import IngestResult
                context.ingest_result = IngestResult(**result.result)
                trace_logger.info(
                    f"Journal ingested - themes: {context.ingest_result.themes}, "
                    f"mood: {context.ingest_result.mood}"
                )
            else:
                error_msg = "Journal ingestion failed"
                context.warnings.append(error_msg)
                trace_logger.error(f"{error_msg}: {result.error}")
                raise ValueError(f"Critical failure: {error_msg}")
                
        except Exception as e:
            trace_logger.error(f"Ingestor exception: {str(e)}")
            raise
    
    async def _call_coaches(self, context: ProcessingContext, trace_logger):
        """Call all philosophy coaches in parallel."""
        
        # Prepare common arguments for all coaches
        coach_args = {
            'summary': context.ingest_result.summary,
            'themes': context.ingest_result.themes,
            'mood': context.ingest_result.mood,
            'question': context.request.question,
            'trace_id': context.trace_id
        }
        
        # Create tasks for parallel execution
        coach_tasks = [
            coach.call_with_timeout(**coach_args)
            for coach in self.coaches
        ]
        
        trace_logger.info(f"Starting {len(coach_tasks)} coach calls in parallel")
        
        # Execute all coach calls in parallel
        results = await asyncio.gather(*coach_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            coach_name = self.coaches[i].name
            
            if isinstance(result, Exception):
                # Handle exceptions from gather
                error_result = AgentCallResult(
                    agent_name=coach_name,
                    success=False,
                    error=f"Exception during coach call: {str(result)}"
                )
                context.agent_results.append(error_result)
                context.warnings.append(f"{coach_name} failed")
                trace_logger.error(f"{coach_name} exception: {str(result)}")
                
            elif isinstance(result, AgentCallResult):
                # Normal agent result
                context.agent_results.append(result)
                
                if result.success:
                    trace_logger.info(f"{coach_name} completed successfully")
                else:
                    context.warnings.append(f"{coach_name} failed")
                    trace_logger.warning(f"{coach_name} failed: {result.error}")
            
            else:
                # Unexpected result type
                error_result = AgentCallResult(
                    agent_name=coach_name,
                    success=False,
                    error=f"Unexpected result type: {type(result)}"
                )
                context.agent_results.append(error_result)
                context.warnings.append(f"{coach_name} returned unexpected result")
                trace_logger.error(f"{coach_name} unexpected result: {type(result)}")
        
        successful_count = sum(1 for r in context.agent_results if r.success)
        trace_logger.info(f"Coach calls completed: {successful_count}/{len(self.coaches)} successful")
        
        # Ensure we have at least one successful result to proceed
        if successful_count == 0:
            trace_logger.error("All coach calls failed")
            # Don't raise here - let composer handle it with warnings


# Additional utility functions for health checks and metrics

async def health_check_agents():
    """Perform health check on all agents."""
    try:
        orchestrator = ReflectionOrchestrator()
        
        # Simple test with minimal journal entry
        test_request = ReflectRequest(
            journal_text="Today I feel grateful for small moments of peace.",
            question=None
        )
        
        # Try to process with a short timeout
        response = await asyncio.wait_for(
            orchestrator.process_reflection(test_request),
            timeout=10.0  # Short timeout for health check
        )
        
        return {
            "status": "healthy",
            "prompts_generated": len(response.prompts),
            "agents_working": True
        }
        
    except asyncio.TimeoutError:
        return {
            "status": "unhealthy",
            "error": "Health check timed out",
            "agents_working": False
        }
    
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "agents_working": False
        }