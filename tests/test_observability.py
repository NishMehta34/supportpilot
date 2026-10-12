import json
import logging
import pytest
from app.observability import observe_run, load_trace, troubleshooting_report


def test_success_return(tmp_path):
    assert observe_run(lambda: {'final_answer': 'ok'}, thread_id='t', model='scripted', request_id='r1', artifact_dir=tmp_path)['final_answer'] == 'ok'


def test_success_trace(tmp_path):
    observe_run(lambda: {}, thread_id='t', model='scripted', request_id='r1', artifact_dir=tmp_path)
    assert load_trace(tmp_path / 'r1.json')['success'] is True


def test_error_is_reraised(tmp_path):
    with pytest.raises(RuntimeError):
        observe_run(lambda: (_ for _ in ()).throw(RuntimeError('private secret')), thread_id='t', model='scripted', request_id='r1', artifact_dir=tmp_path)
    assert load_trace(tmp_path / 'r1.json')['error_type'] == 'RuntimeError'


def test_error_text_not_saved(tmp_path):
    with pytest.raises(ValueError):
        observe_run(lambda: (_ for _ in ()).throw(ValueError('sensitive-token')), thread_id='t', model='scripted', request_id='r1', artifact_dir=tmp_path)
    assert 'sensitive-token' not in (tmp_path / 'r1.json').read_text()


def test_prompt_and_answer_not_saved(tmp_path):
    observe_run(lambda: {'final_answer': 'SECRET', 'trace': [{'tool': 'get_order', 'args': {'token': 'SECRET'}, 'output': 'SECRET'}]}, thread_id='t', model='scripted', request_id='r1', artifact_dir=tmp_path)
    saved = (tmp_path / 'r1.json').read_text()
    assert 'SECRET' not in saved and 'get_order' in saved


def test_invalid_request_id_rejected(tmp_path):
    with pytest.raises(ValueError):
        observe_run(lambda: None, thread_id='t', model='m', request_id='../escape', artifact_dir=tmp_path)


def test_invalid_thread_rejected():
    with pytest.raises(ValueError):
        observe_run(lambda: None, thread_id='', model='m')


def test_no_overwrite(tmp_path):
    observe_run(lambda: None, thread_id='t', model='m', request_id='same', artifact_dir=tmp_path)
    with pytest.raises(FileExistsError):
        observe_run(lambda: None, thread_id='t', model='m', request_id='same', artifact_dir=tmp_path)


def test_report(tmp_path):
    observe_run(lambda: None, thread_id='t', model='m', request_id='a', artifact_dir=tmp_path)
    with pytest.raises(RuntimeError):
        observe_run(lambda: (_ for _ in ()).throw(RuntimeError('bad')), thread_id='t', model='m', request_id='b', artifact_dir=tmp_path)
    r = troubleshooting_report(tmp_path)
    assert (r['runs'], r['successful'], r['failed']) == (2, 1, 1)


def test_structured_log(caplog):
    with caplog.at_level(logging.INFO, logger='supportpilot.observability'):
        observe_run(lambda: None, thread_id='t', model='m', request_id='logged')
    assert any(json.loads(rec.message)['request_id'] == 'logged' for rec in caplog.records)
