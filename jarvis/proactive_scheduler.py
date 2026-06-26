# Source Generated with Decompyle++
# File: proactive_scheduler.cpython-312.pyc (Python 3.12)

'''Lightweight in-process scheduler for briefing nudges and task reminders.'''
from __future__ import annotations
import logging
import os
import subprocess
import threading
import time
from datetime import datetime
logger = logging.getLogger('jarvis.scheduler')
_stop = threading.Event()
_thread: 'threading.Thread | None' = None
_last_briefing_day = ''
_last_nudge_day = ''
_last_consolidation_day = ''
_last_document_reindex_day = ''
_last_flytying_learning_day = ''
_last_briefing_prefetch_day = ''
_last_workflow_nudge_day = ''
_last_reflection_day = ''
_last_service_health_check = 0
_print_status_cache: 'dict[str, str]' = { }
_document_reindex_on_start = False

def _notify(title = None, body = None):
    
    try:
        subprocess.run([
            'notify-send',
            '-a',
            'Jarvis',
            title,
            body[:240]], check = False, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, timeout = 5)
        return None
    except Exception:
        exc = None
        logger.debug('Scheduler notify failed: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _maybe_briefing_prefetch(now = None):
    global _last_briefing_prefetch_day
    if os.getenv('JARVIS_SCHEDULER_BRIEFING_PREFETCH', '1') == '0':
        return None
    
    try:
        hour = int(os.getenv('JARVIS_SCHEDULE_BRIEFING_HOUR', '7'))
        day = now.date().isoformat()
        target = datetime(now.year, now.month, now.day, hour, 0, 0)
        delta_min = (target - now).total_seconds() / 60
        if  < 0, delta_min or 0, delta_min <= 15:
            pass
        else:
            return None
        if _last_briefing_prefetch_day == day:
            return None
        
        try:
            briefing_enabled
            if not briefing_enabled():
                return None
                
                try:
                    from jarvis.assistant_instance import get_assistant
                    import jarvis.morning_briefing
                    assistant = get_assistant()
                    build_briefing = build_briefing
                    import jarvis.morning_briefing
                    build_briefing(journal = assistant.journal, memory_store = assistant.memory, include_news = True)
                    _last_briefing_prefetch_day = day
                    logger.info('Briefing prefetched for %s', day)
                    return None
                    except ValueError:
                        hour = 7
                        continue
                except Exception:
                    exc = None
                    logger.debug('Briefing prefetch skipped: %s', exc)
                    exc = None
                    del exc
                    return None
                    exc = None
                    del exc





def _maybe_workflow_time_nudge(now = None):
    global _last_workflow_nudge_day
    if os.getenv('JARVIS_SCHEDULER_WORKFLOW_NUDGE', '1') == '0':
        return None
    day = now.date().isoformat()
    if _last_workflow_nudge_day == day:
        return None
    
    try:
        _load_watch = _load_watch
        list_workflows = list_workflows
        import jarvis.workflow_learning
        state = _load_watch()
        hour_key = f'''{now.hour:02d}'''
        for wf in list_workflows()[:20]:
            if not wf.get('slug'):
                wf.get('slug')
            slug = ''
            if not wf.get('steps'):
                wf.get('steps')
            steps = []
            if not steps:
                continue
            if not steps[0].get('action'):
                steps[0].get('action')
            first = ''.lower()
            if 'work' not in slug and first not in ('scene_recall', 'ha_scene'):
                continue
            if not state.get('patterns'):
                state.get('patterns')
            patterns = { }
            for pid, entry in patterns.items():
                if not entry.get('count'):
                    entry.get('count')
                if int(0) < 3:
                    continue
                if not entry.get('last_seen'):
                    entry.get('last_seen')
                last = ''
                if not last:
                    continue
                    
                    try:
                        if not last[11:13] == hour_key:
                            continue
                            
                            try:
                                _last_workflow_nudge_day = day
                                _notify('ARIA', f'''Run **{wf.get('name', slug)}**? (usual time)''')
                                logger.info('Workflow time nudge: %s', slug)
                                patterns.items()
                                list_workflows()[:20]
                                return None
                                
                                try:
                                    continue
                                    return None
                                except Exception:
                                    exc = None
                                    logger.debug('Workflow nudge skipped: %s', exc)
                                    exc = None
                                    del exc
                                    return None
                                    exc = None
                                    del exc






def _maybe_print_job_watch(now = None):
    
    try:
        list_jobs = list_jobs
        import jarvis.engineering.print_jobs
        emit = emit
        import jarvis.events
        jobs = list_jobs(limit = 10)
        for job in jobs:
            if not job.get('id'):
                job.get('id')
            jid = ''
            if not job.get('status'):
                job.get('status')
            status = ''.lower()
            prev = _print_status_cache.get(jid)
            _print_status_cache[jid] = status
            if not prev:
                continue
                
                try:
                    if not prev != status:
                        continue
                        
                        try:
                            if not job.get('message'):
                                job.get('message')
                            emit('print_job_update', job_id = jid, status = status, message = '', notify_complete = status in ('handoff', 'printing'))
                            continue
                            return None
                        except Exception:
                            exc = None
                            logger.debug('Print job watch skipped: %s', exc)
                            exc = None
                            del exc
                            return None
                            exc = None
                            del exc





def _maybe_flytying_learning(now = None):
    global _last_flytying_learning_day
    day = now.date().isoformat()
    if _last_flytying_learning_day == day:
        return None
    
    try:
        nightly_enabled = nightly_enabled
        run_scheduled = run_scheduled
        import jarvis.flytying.nightly
        if not nightly_enabled():
            return None
            
            try:
                memory = None
                
                try:
                    get_assistant = get_assistant
                    import jarvis.assistant_instance
                    memory = get_assistant().memory
                    
                    try:
                        result = run_scheduled(now, memory = memory)
                        if result.get('ok'):
                            if not result.get('skipped'):
                                _last_flytying_learning_day = day
                                logger.info('Fly-tying nightly learning: %s', result.get('message', 'done'))
                                return None
                            return None
                        return None
                        except Exception:
                            
                            try:
                                continue
                                
                                try:
                                    pass
                                except Exception:
                                    exc = None
                                    logger.debug('Fly-tying learning tick skipped: %s', exc)
                                    exc = None
                                    del exc
                                    return None
                                    exc = None
                                    del exc








def _maybe_reflection(now = None):
    global _last_reflection_day
    day = now.date().isoformat()
    if _last_reflection_day == day:
        return None
    
    try:
        reflection_enabled = reflection_enabled
        run_scheduled = run_scheduled
        import jarvis.reflection_loop
        if not reflection_enabled():
            return None
            
            try:
                result = run_scheduled(now)
                if result:
                    if result.get('ok'):
                        if not result.get('skipped'):
                            _last_reflection_day = day
                            return None
                        return None
                    return None
                return None
            except Exception:
                exc = None
                logger.debug('Reflection tick skipped: %s', exc)
                exc = None
                del exc
                return None
                exc = None
                del exc




def _maybe_service_health(now = None):
    global _last_service_health_check
    if time.time() - _last_service_health_check < 300:
        return None
    _last_service_health_check = time.time()
    
    try:
        check_services_health = check_services_health
        import jarvis.interrupt_policy
        get_status = get_status
        import jarvis.services
        check_services_health(get_status())
        return None
    except Exception:
        exc = None
        logger.debug('Service health interrupt skipped: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc



def _maybe_briefing(now = None):
    global _last_briefing_day
    if os.getenv('JARVIS_SCHEDULER_BRIEFING', '1') == '0':
        return None
    
    try:
        hour = int(os.getenv('JARVIS_SCHEDULE_BRIEFING_HOUR', '7'))
        day = now.date().isoformat()
        if now.hour != hour or _last_briefing_day == day:
            return None
        briefing_enabled = briefing_enabled
        should_show_launch_briefing = should_show_launch_briefing
        import jarvis.morning_briefing
        if not briefing_enabled() or should_show_launch_briefing(day = day):
            return None
        _last_briefing_day = day
        _notify('ARIA', "Good morning — open ARIA for today's briefing.")
        logger.info('Proactive briefing nudge sent for %s', day)
        return None
    except ValueError:
        hour = 7
        continue



def _maybe_task_nudge(now = None):
    global _last_nudge_day
    if os.getenv('JARVIS_SCHEDULER_NUDGE', '1') == '0':
        return None
    
    try:
        hour = int(os.getenv('JARVIS_SCHEDULE_NUDGE_HOUR', '10'))
        day = now.date().isoformat()
        if now.hour != hour and now.minute > 5 or _last_nudge_day == day:
            return None
        
        try:
            task_nudge_check = task_nudge_check
            import jarvis.movie_tiers
            nudge = task_nudge_check()
            if nudge.get('nudge'):
                if nudge.get('message'):
                    mark_task_nudge_shown = mark_task_nudge_shown
                    import jarvis.movie_tiers
                    mark_task_nudge_shown()
                    _last_nudge_day = day
                    _notify('ARIA tasks', str(nudge['message']).replace('**', '').replace('_', '')[:200])
                    logger.info('Task nudge sent')
                    return None
                return None
            return None
            except ValueError:
                hour = 10
                continue
        except Exception:
            exc = None
            logger.debug('Task nudge skipped: %s', exc)
            exc = None
            del exc
            return None
            exc = None
            del exc




def _maybe_planner_tick(now = None):
    
    try:
        planner_enabled = planner_enabled
        import jarvis.feature_flags
        if not planner_enabled():
            return None
            
            try:
                tick_alarms_and_timers = tick_alarms_and_timers
                import jarvis.planner_store
                for note in tick_alarms_and_timers():
                    _notify('ARIA planner', note.get('message', 'Reminder'))
                return None
            except Exception:
                exc = None
                logger.debug('Planner tick skipped: %s', exc)
                exc = None
                del exc
                return None
                exc = None
                del exc




def _maybe_document_reindex(now = None):
    global _document_reindex_on_start, _last_document_reindex_day
    if os.getenv('JARVIS_SCHEDULER_DOCUMENT_REINDEX', '1') == '0':
        return None
    
    try:
        build_index = build_index
        index_needs_rebuild = index_needs_rebuild
        last_index_warnings = last_index_warnings
        import jarvis.documents_rag
        if _document_reindex_on_start:
            _document_reindex_on_start = False
            if index_needs_rebuild():
                chunks = build_index(force = True)
                warnings = last_index_warnings()
                logger.info('Document library reindexed on startup: %d chunks%s', len(chunks), f''' ({len(warnings)} warning(s))''' if warnings else '')
            return None
        
        try:
            hour = int(os.getenv('JARVIS_DOCUMENT_REINDEX_HOUR', '4'))
            
            try:
                day = now.date().isoformat()
                if now.hour != hour and now.minute > 5 or _last_document_reindex_day == day:
                    return None
                    
                    try:
                        if index_needs_rebuild():
                            chunks = build_index(force = True)
                            logger.info('Scheduled document reindex: %d chunks', len(chunks))
                        _last_document_reindex_day = day
                        return None
                        except ValueError:
                            hour = 4
                            
                            try:
                                continue
                                
                                try:
                                    pass
                                except Exception:
                                    exc = None
                                    logger.debug('Document reindex tick skipped: %s', exc)
                                    exc = None
                                    del exc
                                    return None
                                    exc = None
                                    del exc








def _maybe_memory_consolidation(now = None):
    pass
# WARNING: Decompyle incomplete


def _loop():
    if not _stop.wait(60):
        
        try:
            now = datetime.now()
            _maybe_briefing_prefetch(now)
            _maybe_briefing(now)
            _maybe_task_nudge(now)
            _maybe_workflow_time_nudge(now)
            _maybe_print_job_watch(now)
            _maybe_project_journals(now)
            _maybe_knowledge_research(now)
            _maybe_flytying_learning(now)
            _maybe_reflection(now)
            _maybe_planner_tick(now)
            _maybe_document_reindex(now)
            _maybe_memory_consolidation(now)
            _maybe_service_health(now)
            if not _stop.wait(60):
                continue
            return None
            return None
        except Exception:
            exc = None
            logger.warning('Scheduler tick failed: %s', exc)
            exc = None
            del exc
            continue
            exc = None
            del exc



def _maybe_project_journals(now = None):
    
    try:
        run_scheduled_daily = run_scheduled_daily
        import jarvis.project_journal_daily
        memory = None
        
        try:
            get_assistant = get_assistant
            import jarvis.assistant_instance
            memory = get_assistant().memory
            
            try:
                results = run_scheduled_daily(now, memory = memory)
                for r in results:
                    if not r.get('ok'):
                        continue
                        
                        try:
                            if r.get('skipped'):
                                continue
                                
                                try:
                                    logger.info('Project journal daily %s %s (%s)', r.get('slug'), r.get('phase'), r.get('day'))
                                    continue
                                    return None
                                    except Exception:
                                        
                                        try:
                                            continue
                                            
                                            try:
                                                pass
                                            except Exception:
                                                exc = None
                                                logger.debug('Project journal daily tick skipped: %s', exc)
                                                exc = None
                                                del exc
                                                return None
                                                exc = None
                                                del exc









def _maybe_knowledge_research(now = None):
    
    try:
        run_scheduled = run_scheduled
        import jarvis.knowledge_research_daily
        memory = None
        
        try:
            get_assistant = get_assistant
            import jarvis.assistant_instance
            memory = get_assistant().memory
            
            try:
                results = run_scheduled(now, memory = memory)
                for r in results:
                    if not isinstance(r, dict):
                        continue
                        
                        try:
                            if not r.get('ok'):
                                continue
                                
                                try:
                                    if r.get('skipped'):
                                        continue
                                        
                                        try:
                                            if r.get('slug'):
                                                logger.info('Knowledge research %s (%s)', r.get('slug'), r.get('day'))
                                                continue
                                            if not r.get('message'):
                                                continue
                                                
                                                try:
                                                    logger.info('Knowledge research: %s', r.get('message'))
                                                    continue
                                                    return None
                                                    except Exception:
                                                        
                                                        try:
                                                            continue
                                                            
                                                            try:
                                                                pass
                                                            except Exception:
                                                                exc = None
                                                                logger.debug('Knowledge research tick skipped: %s', exc)
                                                                exc = None
                                                                del exc
                                                                return None
                                                                exc = None
                                                                del exc











def start():
    global _document_reindex_on_start, _thread
    if os.getenv('JARVIS_SCHEDULER', '1') == '0':
        return None
    if _thread and _thread.is_alive():
        return None
    
    try:
        install_hooks = install_hooks
        import jarvis.interrupt_policy
        install_hooks()
        _stop.clear()
        _document_reindex_on_start = True
        _thread = threading.Thread(target = _loop, daemon = True, name = 'jarvis-scheduler')
        _thread.start()
        logger.info('Proactive scheduler started')
        return None
    except Exception:
        exc = None
        logger.debug('Interrupt hooks skipped: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc



def stop():
    _stop.set()
    if _thread:
        _thread.join(timeout = 2)
        return None

