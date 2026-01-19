#!/usr/bin/env python3
import json
import sys
from collections import defaultdict

def summarize_terraform_plan(plan_file):
    with open(plan_file, 'r') as f:
        plan = json.load(f)
    
    summary = []
    summary.append("# Terraform Plan Summary\n")
    
    # Plan metadata
    summary.append(f"**Terraform Version:** {plan.get('terraform_version', 'Unknown')}")
    summary.append(f"**Format Version:** {plan.get('format_version', 'Unknown')}\n")
    
    # Resource changes summary
    resource_changes = plan.get('resource_changes', [])
    actions_count = defaultdict(int)
    
    for change in resource_changes:
        for action in change.get('change', {}).get('actions', []):
            actions_count[action] += 1
    
    summary.append("## Resource Changes Overview")
    summary.append(f"- **Create:** {actions_count.get('create', 0)} resources")
    summary.append(f"- **Update:** {actions_count.get('update', 0)} resources") 
    summary.append(f"- **Delete:** {actions_count.get('delete', 0)} resources")
    summary.append(f"- **Replace:** {actions_count.get('create', 0) if actions_count.get('delete', 0) > 0 else 0} resources\n")
    
    # Group resources by module and action
    modules = defaultdict(lambda: defaultdict(list))
    
    for change in resource_changes:
        address = change.get('address', '')
        module_name = address.split('.')[0] if '.' in address else 'root'
        resource_type = change.get('type', '')
        resource_name = change.get('name', '')
        actions = change.get('change', {}).get('actions', [])
        
        for action in actions:
            modules[module_name][action].append(f"{resource_type}.{resource_name}")
    
    # Output by module
    summary.append("## Changes by Module\n")
    
    for module, actions in sorted(modules.items()):
        summary.append(f"### {module}")
        
        for action, resources in sorted(actions.items()):
            if resources:
                action_emoji = {
                    'create': '➕',
                    'update': '🔄', 
                    'delete': '❌',
                    'read': '📖'
                }.get(action, '🔧')
                
                summary.append(f"\n**{action_emoji} {action.title()}:**")
                for resource in sorted(resources):
                    summary.append(f"- {resource}")
        summary.append("")
    
    # Output variables
    variables = plan.get('variables', {})
    if variables:
        summary.append("## Variables")
        for var_name, var_data in sorted(variables.items()):
            value = var_data.get('value', 'Not set')
            if 'password' in var_name.lower() or 'token' in var_name.lower():
                value = '[SENSITIVE]'
            summary.append(f"- **{var_name}:** {value}")
        summary.append("")
    
    # Output planned values (key outputs)
    planned_values = plan.get('planned_values', {})
    outputs = planned_values.get('outputs', {})
    
    if outputs:
        summary.append("## Key Outputs")
        for output_name, output_data in sorted(outputs.items()):
            if not output_data.get('sensitive', False):
                value = output_data.get('value', 'Unknown')
                summary.append(f"- **{output_name}:** {value}")
        summary.append("")
    
    return '\n'.join(summary)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python summarize_plan.py <plan.json>")
        sys.exit(1)
    
    plan_file = sys.argv[1]
    try:
        summary = summarize_terraform_plan(plan_file)
        print(summary)
    except Exception as e:
        print(f"Error processing plan file: {e}")
        sys.exit(1)