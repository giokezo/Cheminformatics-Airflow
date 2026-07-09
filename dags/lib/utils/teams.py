import logging
from urllib.parse import urlencode

import requests
from airflow.hooks.base import BaseHook

WEBHOOK_CONN_ID = 'msteams_webhook'


def get_webhook_url(conn_id=WEBHOOK_CONN_ID):
    """Reconstruct a webhook URL from an Airflow connection.

    The secret lives in the connection (provisioned via env), never in code, and is masked by
    Airflow in task logs. Returns ``None`` when the connection is not configured, so callers can
    degrade to logging instead of failing in local/dev.
    """
    try:
        conn = BaseHook.get_connection(conn_id)
    except Exception:
        logging.warning(f'Teams webhook connection {conn_id!r} is not configured; skipping alert.')
        return None

    scheme = conn.conn_type or 'https'
    netloc = conn.host
    if conn.port:
        netloc = f'{netloc}:{conn.port}'
    url = f'{scheme}://{netloc}/{conn.schema or ""}'
    extra = conn.extra_dejson
    if extra:
        url = f'{url}?{urlencode(extra)}'
    return url


def _post_card(body):
    """Post an Adaptive Card body to Teams. No-op (logs) when no webhook is configured."""
    webhook_url = get_webhook_url()
    message = {
        'type': 'message',
        'attachments': [
            {
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': {
                    '$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
                    'type': 'AdaptiveCard',
                    'version': '1.4',
                    'body': body,
                },
            }
        ],
    }

    if not webhook_url:
        logging.info(f'[teams no-op] {message}')
        return

    # Notifications are best-effort: an unreachable/misconfigured webhook must never fail the task.
    try:
        response = requests.post(webhook_url, json=message, timeout=30)
    except requests.RequestException as error:
        logging.error(f'Could not reach Teams webhook: {error}')
        return

    # Teams incoming webhooks return 200; Power Automate flows return 202 Accepted — both are success.
    if response.ok:
        logging.info(f'Teams message sent successfully ({response.status_code})')
    else:
        logging.error(f'Failed to send message to Teams: {response.status_code} {response.text}')


def _text_block(text, **kwargs):
    return {'type': 'TextBlock', 'text': text, 'wrap': True, **kwargs}


def _fact_set(facts):
    return {'type': 'FactSet', 'facts': [{'title': title, 'value': str(value)} for title, value in facts]}


def send_teams_alert(context):
    """``on_failure_callback`` that posts the failed task to MS Teams."""
    task_instance = context['task_instance']
    _post_card([
        _text_block('🚨 **Airflow Task Failed!**', weight='Bolder', color='Attention', size='Medium'),
        _fact_set([
            ('DAG', task_instance.dag_id),
            ('Task', task_instance.task_id),
            ('Run', task_instance.run_id),
        ]),
    ])


def send_success_card(title, facts):
    """Post a green success/summary card. ``facts`` is a list of (title, value) tuples."""
    _post_card([
        _text_block(f'✅ **{title}**', weight='Bolder', color='Good', size='Medium'),
        _fact_set(facts),
    ])
