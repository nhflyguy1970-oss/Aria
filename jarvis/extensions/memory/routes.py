# Source Generated with Decompyle++
# File: routes.cpython-312.pyc (Python 3.12)

'''Memory fast-path routing rules.'''
from __future__ import annotations
import re
from jarvis.explicit_teaching import is_teach_recall, parse_teach_message, parse_teach_recall_query
from jarvis.document_learning import is_document_learn_recall, is_ingest_document, is_learn_from_document, parse_document_learn_recall_query, parse_url_from_message
from jarvis.observation_learning import is_observation_recall, is_observe_camera, is_observe_last_command, is_observe_log, is_observe_screenshot, is_observe_terminal, parse_observation_recall_query
from jarvis.correction_learning import is_correction_message, is_correction_recall, parse_correction_recall_query
from jarvis.experience_memory import parse_experience_recall_query
from jarvis.relationship_memory import parse_relationship_recall_query
from jarvis.router_table import RouteRule

def _is_memory_about_user(lower = None):
    return bool(re.search('\\b(something i like|what do i like|things? i like|my hobbies|my interests|what do i enjoy|tell me something about me|what do you know about me|about me\\b|who am i\\b|tell me about myself)\\b', lower))


def _remember_text(message = None):
    text = re.sub("^(please\\s+)?(remember|don't forget|note that|keep in mind)\\s*(that\\s+)?", '', message, flags = re.I).strip()
    return re.sub('^(these|the following)\\s+facts?\\s*:?\\s*', '', text, flags = re.I).strip()


def _is_memory_correct_route(message = None, lower = None):
    if not re.search('\\b(correct|update|fix)\\s+(that|the fact|memory|my memory)\\b', lower):
        re.search('\\b(correct|update|fix)\\s+(that|the fact|memory|my memory)\\b', lower)
    return bool(re.search('^(?:please\\s+)?actually,?\\s+', lower))


def _memory_correct_params(message = None):
    parse_memory_correct = parse_memory_correct
    import jarvis.trust_memory
    parsed = parse_memory_correct(message)
    if parsed:
        (hint, new_fact) = parsed
        return {
            'new_fact': new_fact,
            'search_hint': hint }


def memory_routes():
    return [
        RouteRule('correction_recall', 8, 'correction recall', (lambda m, lower, _s: is_correction_recall(lower)), params = (lambda m: {
'query': parse_correction_recall_query(m) })),
        RouteRule('correction_learn', 9, 'correction learn', (lambda m, lower, _s: if is_correction_message(m):
is_correction_message(m)if not is_correction_recall(lower):
not is_correction_recall(lower)not _is_memory_correct_route(m, lower)), params = (lambda m: {
'text': m })),
        RouteRule('observation_recall', 9, 'observation recall', (lambda m, lower, _s: is_observation_recall(lower)), params = (lambda m: {
'query': parse_observation_recall_query(m) })),
        RouteRule('observe_camera', 9, 'observe camera', (lambda m, lower, _s: is_observe_camera(m)), params = (lambda m: { })),
        RouteRule('observe_screenshot', 9, 'observe screenshot', (lambda m, lower, _s: is_observe_screenshot(m)), params = (lambda m: { })),
        RouteRule('observe_terminal', 10, 'observe terminal', (lambda m, lower, _s: if not is_observe_terminal(m):
is_observe_terminal(m)is_observe_last_command(m)), params = (lambda m: { })),
        RouteRule('observe_log', 10, 'observe log', (lambda m, lower, _s: is_observe_log(m)), params = (lambda m: { })),
        RouteRule('document_learn_recall', 10, 'document learn recall', (lambda m, lower, _s: is_document_learn_recall(lower)), params = (lambda m: {
'query': parse_document_learn_recall_query(m) })),
        RouteRule('learn_from_url', 10, 'learn from url', (lambda m, lower, _s: if parse_url_from_message(m):
parse_url_from_message(m)bool(is_learn_from_document(m))), params = (lambda m: {
'url': parse_url_from_message(m) })),
        RouteRule('ingest_document', 11, 'ingest document', (lambda m, lower, _s: is_ingest_document(m)), params = (lambda m: {
'url': parse_url_from_message(m),
'path': '' })),
        RouteRule('learn_from_document', 11, 'learn from document', (lambda m, lower, _s: if is_learn_from_document(m):
is_learn_from_document(m)not parse_url_from_message(m)), params = (lambda m: {
'path': '',
'ocr': bool(re.search('\\b(ocr|scanned|scan(ned)?)\\b', m, re.I)) })),
        RouteRule('teach_recall', 11, 'teach recall', (lambda m, lower, _s: is_teach_recall(lower)), params = (lambda m: {
'query': parse_teach_recall_query(m) })),
        RouteRule('teach', 12, 'explicit teach', (lambda m, lower, _s: if parse_teach_message(m):
parse_teach_message(m)bool(not is_teach_recall(lower))), params = (lambda m: {
'text': m })),
        RouteRule('relationship_recall', 13, 'relationship recall', (lambda m, lower, _s: bool(re.search("\\b(connections?|relationships?|relationship graph|what(?:'s| is) connected to|who works on|who uses|linked to)\\b", lower))), params = (lambda m: if not parse_relationship_recall_query(m):
parse_relationship_recall_query(m){
'query': m })),
        RouteRule('experience_recall', 14, 'experience recall', (lambda m, lower, _s: bool(re.search('\\b(what worked|what failed|past failures|past successes|experiences? (?:for|with|about)|recall experiences?)\\b', lower))), params = (lambda m: if not parse_experience_recall_query(m):
parse_experience_recall_query(m){
'query': m })),
        RouteRule('memory_about_user', 15, 'user profile', (lambda m, lower, _s: _is_memory_about_user(lower)), params = (lambda m: {
'question': m })),
        RouteRule('recall', 16, 'recall memories', (lambda m, lower, _s: bool(re.search('\\b(what do you remember|recall|my memories)\\b', lower)))),
        RouteRule('memory_search', 17, 'memory search', (lambda m, lower, _s: bool(re.search('\\b(search my memory|search memory|find in memory|memory search)\\b', lower))), params = (lambda m: if not re.sub('^(please\\s+)?(search my memory|search memory|find in memory|memory search)\\s*(for\\s+)?', '', m, flags = re.I).strip():
re.sub('^(please\\s+)?(search my memory|search memory|find in memory|memory search)\\s*(for\\s+)?', '', m, flags = re.I).strip(){
'query': m })),
        RouteRule('memory_forget', 18, 'forget memory', (lambda m, lower, _s: bool(re.search('\\b(forget|delete memory|remove memory)\\b', lower))), params = (lambda m: if not re.sub('^(please\\s+)?(forget|delete memory|remove memory)\\s*(about\\s+)?', '', m, flags = re.I).strip():
re.sub('^(please\\s+)?(forget|delete memory|remove memory)\\s*(about\\s+)?', '', m, flags = re.I).strip(){
'query': m })),
        RouteRule('memory_correct', 19, 'correct memory', (lambda m, lower, _s: if not re.search('\\b(correct|update|fix)\\s+(that|the fact|memory|my memory)\\b', lower):
re.search('\\b(correct|update|fix)\\s+(that|the fact|memory|my memory)\\b', lower)bool(re.search('^(?:please\\s+)?actually,?\\s+', lower))), params = _memory_correct_params),
        RouteRule('memory_summarize', 20, 'summarize to memory', (lambda m, lower, _s: bool(re.search('\\b(summarize (this )?conversation to memory|remember (this|our) conversation|save conversation to memory)\\b', lower)))),
        RouteRule('memory_namespace', 21, 'memory namespace', (lambda m, lower, _s: bool(re.search('\\b(set memory namespace|memory namespace)\\b', lower))), params = (lambda m: mobj = re.search('\\b(?:namespace|project)\\s+[`\'\\"]?(\\w[\\w-]*)[`\'\\"]?', m, re.I)if re.search('\\b(?:namespace|project)\\s+[`\'\\"]?(\\w[\\w-]*)[`\'\\"]?', m, re.I):
{
'namespace': mobj.group(1) }{
None: '' })),
        RouteRule('memory_prune', 22, 'prune memory', (lambda m, lower, _s: bool(re.search('\\bprune (stale )?memor', lower)))),
        RouteRule('cheatsheet_list', 23, 'cheatsheet list', (lambda m, lower, _s: bool(re.search('\\b(list|show|what)\\s+cheatsheets?\\b', lower)))),
        RouteRule('cheatsheet_reset', 24, 'reset cheatsheet', (lambda m, lower, _s: bool(re.search('\\b(reset|restore)\\s+.*cheatsheets?\\b', lower))), params = (lambda m: _cheatsheet_key_params(m))),
        RouteRule('cheatsheet_show', 25, 'cheatsheet show', (lambda m, lower, _s: bool(re.search('\\bcheat\\s*sheets?\\b', lower))), params = (lambda m: _cheatsheet_key_params(m))),
        RouteRule('project_checkpoint', 26, 'project checkpoint', (lambda m, lower, _s: bool(re.search('\\b(save (where i left off|project checkpoint|my progress)|remember where i left off|checkpoint (my )?project)\\b', lower)))),
        RouteRule('project_resume', 27, 'project resume', (lambda m, lower, _s: bool(re.search('\\b(where did i leave off|what was i working on|resume (my )?project|catch me up on (the )?project)\\b', lower)))),
        RouteRule('remember', 28, 'remember fact', (lambda m, lower, _s: if re.search("\\b(remember|don't forget|note that|keep in mind)\\b", lower):
re.search("\\b(remember|don't forget|note that|keep in mind)\\b", lower)if not _is_memory_about_user(lower):
not _is_memory_about_user(lower)if not re.search('\\bremember (this|our) conversation\\b', lower):
not re.search('\\bremember (this|our) conversation\\b', lower)if not re.search('\\bremember where i left off\\b', lower):
not re.search('\\bremember where i left off\\b', lower)bool(not re.search('\\bremember journal\\b', lower))), params = (lambda m: {
'text': _remember_text(m) }))]


def _cheatsheet_key_params(message = None):
    resolve_key_from_message = resolve_key_from_message
    import jarvis.cheatsheets
    if not resolve_key_from_message(message):
        resolve_key_from_message(message)
    return {
        'key': '' }

