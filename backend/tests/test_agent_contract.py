import json
import time
import uuid
from types import SimpleNamespace
from openai.types.chat import ChatCompletionMessage
from database.connection import SessionLocal
from context_app.models import AgentRun, UsageBudget
from context_app.agent import run_agent
from conftest import demo, sync


def test_model_tool_loop_persists_cited_task_without_real_provider(reviewer, monkeypatch):
    client, user = reviewer
    sid = demo(client)
    fid = f'shipment:{sid}:field:GROSS_WEIGHT'
    evidence = client.get(f'/api/shipments/{sid}/context-evidence', params={'field_id': fid}).json()['evidence']
    aid = evidence[0]['assertion_id']
    monkeypatch.setenv('OPENAI_AGENT_MODEL', 'scripted-test-model')
    monkeypatch.setenv('AGENT_BUDGET_USD', '1')
    monkeypatch.setenv('MODEL_INPUT_USD_PER_MILLION', '1')
    monkeypatch.setenv('MODEL_OUTPUT_USD_PER_MILLION', '1')
    with SessionLocal() as db:
        db.query(UsageBudget).delete()
        rid = str(uuid.uuid4())
        db.add(AgentRun(id=rid, dossier_id=sid, actor_id=user['id'], revision=1, status='running',
            question='Investigate this conflict', result={}, created_at=int(time.time()), updated_at=int(time.time())))
        db.commit()
    class ScriptedModel:
        def __init__(self):
            self.chat = SimpleNamespace(completions=self)
            self.calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                name, args = 'get_field_evidence', {'field_id': fid}
            elif self.calls == 2:
                name, args = 'propose_review_task', {'field_id': fid, 'evidence_ids': [aid], 'reason': 'Review the cited source.'}
            else:
                assert kwargs['tool_choice'] == 'none'
                msg = ChatCompletionMessage(role='assistant', content=json.dumps({'answer': 'The cited source needs review.',
                    'cited_assertion_ids': [aid], 'uncertainties': ['No physical weight was verified.']}))
                return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50))
            msg = ChatCompletionMessage(role='assistant', content=None, tool_calls=[{'id': str(self.calls), 'type': 'function',
                'function': {'name': name, 'arguments': json.dumps(args)}}])
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50))
    run_agent(rid, user, client=ScriptedModel())
    result = client.get(f'/api/shipments/{sid}/agent-runs/{rid}').json()
    assert result['status'] == 'completed', result
    assert result['result']['citations'][0]['assertion_id'] == aid
    assert result['result']['proposed_action']['status'] == 'pending'
    assert result['result']['usage']['input_tokens'] == 300
    assert [t['tool'] for t in result['result']['tool_events']] == ['get_field_evidence', 'propose_review_task']
    sync(sid)
    assert len(client.get(f'/api/shipments/{sid}/context-status').json()['tasks']) == 1


def test_one_bounded_final_repair_does_not_repeat_proposal(reviewer, monkeypatch):
    client, user = reviewer
    sid = demo(client)
    fid = f'shipment:{sid}:field:GROSS_WEIGHT'
    evidence = client.get(f'/api/shipments/{sid}/context-evidence', params={'field_id': fid}).json()['evidence']
    aid = evidence[0]['assertion_id']
    for name, value in {'OPENAI_AGENT_MODEL': 'scripted-repair-test', 'AGENT_BUDGET_USD': '1', 'MODEL_INPUT_USD_PER_MILLION': '1', 'MODEL_OUTPUT_USD_PER_MILLION': '1'}.items():
        monkeypatch.setenv(name, value)
    rid = str(uuid.uuid4())
    with SessionLocal() as db:
        db.query(UsageBudget).delete()
        db.add(AgentRun(id=rid, dossier_id=sid, actor_id=user['id'], revision=1, status='running', question='Investigate', result={}, created_at=int(time.time()), updated_at=int(time.time())))
        db.commit()
    class Provider:
        def __init__(self): self.chat = SimpleNamespace(completions=self); self.calls = 0
        def create(self, **kwargs):
            self.calls += 1
            if self.calls <= 2:
                name, args = ('get_field_evidence', {'field_id': fid}) if self.calls == 1 else ('propose_review_task', {'field_id': fid, 'evidence_ids': [aid], 'reason': 'Review this source.'})
                message = ChatCompletionMessage(role='assistant', content=None, tool_calls=[{'id': str(self.calls), 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}])
            else:
                assert kwargs['tool_choice'] == 'none'
                text = 'Unsupported 999999 kg' if self.calls == 3 else 'The cited source needs review.'
                message = ChatCompletionMessage(role='assistant', content=json.dumps({'answer': text, 'cited_assertion_ids': [aid], 'uncertainties': []}))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50))
    provider = Provider()
    run_agent(rid, user, client=provider)
    result = client.get(f'/api/shipments/{sid}/agent-runs/{rid}').json()
    assert result['status'] == 'completed' and result['result']['final_repair_attempted']
    assert provider.calls == 4
    assert result['result']['usage']['input_tokens'] == 400
    assert len(client.get(f'/api/shipments/{sid}/context-status').json()['tasks']) == 1
