import re
from typing import Dict, List

def extract_artifact(content: str) -> Dict:
    """Extract artifact and actions from LLM response"""
    if not content:
        return None
        
    # Find artifact with attributes
    artifact_match = re.search(r'<artifact([^>]*)>(.*?)</artifact>', content, re.DOTALL)
    if not artifact_match:
        return None
    
    attrs_str = artifact_match.group(1)
    artifact_content = artifact_match.group(2)
    
    # Extract attributes
    artifact_id = None
    artifact_title = None
    
    id_match = re.search(r'id="([^"]*)"', attrs_str)
    title_match = re.search(r'title="([^"]*)"', attrs_str)
    
    if id_match:
        artifact_id = id_match.group(1)
    if title_match:
        artifact_title = title_match.group(1)
    
    # Extract actions in the order they appear (CRITICAL for proper execution)
    actions = []
    
    # Combined pattern to find all actions in document order
    # Support both filePath and filepath for compatibility
    action_pattern = r'<action\s+type="(file|shell)"(?:\s+(?:filePath|filepath)="([^"]+)")?\s*>(.*?)</action>'
    
    for match in re.finditer(action_pattern, artifact_content, re.DOTALL):
        action_type = match.group(1)
        filepath = match.group(2)  # Only exists for file type
        content = match.group(3)
        
        if action_type == 'file':
            actions.append({
                'type': 'file',
                'filePath': filepath,
                'content': content.strip()
            })
        elif action_type == 'shell':
            actions.append({
                'type': 'shell',
                'command': content.strip()
            })
    
    return {
        'id': artifact_id,
        'title': artifact_title,
        'actions': actions
    }
