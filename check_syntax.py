import ast, os
os.chdir(r'C:\Users\hp\Desktop\salary management system')
files = [
    'main.py','database.py','config.py',
    'utils/security.py','utils/calculations.py','utils/validators.py',
    'agents/orchestrator.py','agents/analytics_agent.py',
    'agents/report_agent.py','agents/payroll_agent.py',
    'components/sidebar.py','components/dashboard.py',
    'components/employee_ui.py','components/payroll_ui.py',
    'components/attendance_ui.py','components/analytics_ui.py',
    'components/reports_ui.py','components/settings_ui.py',
    'components/ai_chat.py',
]
ok, fail = [], []
for f in files:
    if os.path.exists(f):
        try:
            ast.parse(open(f, encoding='utf-8').read())
            ok.append(f)
        except SyntaxError as e:
            fail.append(f'{f}: {e}')
    else:
        fail.append(f'{f}: FILE NOT FOUND')
print(f'PASS: {len(ok)} / {len(files)}')
print(f'FAIL: {len(fail)}')
for x in fail:
    print(f'  X  {x}')
if not fail:
    print('ALL FILES PASS SYNTAX CHECK!')
