import re


def _slugify_code(env, name, number):
    slug = re.sub(r'[^A-Za-z0-9]', '', name or '').upper()[:5]
    code = slug or 'TEAM'
    candidate = code
    while env['maintenance.team'].sudo().with_context(active_test=False).search_count(
            [('code', '=', candidate)]):
        candidate = f'{code}{number}'
        number += 1
    return candidate


def post_init_hook(env):
    """Backfill team codes so legacy teams get their request sequence."""
    teams = env['maintenance.team'].sudo().search([('code', 'in', [False])])
    for number, team in enumerate(teams, start=1):
        team.code = _slugify_code(env, team.name, number)
        team._ensure_request_sequence()
