import os
import re

path = r"c:\Users\Arvin\Documents\AgriDjangoPortal\templates\candidate_apply_edit.html"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make core replacements
content = content.replace("Confirm Application", "Edit Application")
content = content.replace("Confirm Your Application", "Your Application Details")
content = content.replace("{% url 'program_detail' program.id %}", "{% url 'profile' %}")
content = content.replace("Back to Program", "Back to My Applications")
content = content.replace("{{ program.", "{{ candidate.program.")
content = content.replace('{% if program.', '{% if candidate.program.')
content = content.replace("{{ user.first_name }}", "{{ candidate.first_name }}")
content = content.replace("{{ user.last_name }}", "{{ candidate.last_name }}")
content = content.replace("{{ user.email }}", "{{ candidate.email }}")
content = content.replace("{{ user.username }}", "{{ candidate.created_by.username }}")
content = content.replace("profile.", "candidate.")

# JS fetch endpoint change
content = content.replace("{% url \"profile\" %}", "{% url 'edit_candidate' candidate.id %}")

# Modify the warning message about "You can still submit your application..."
content = content.replace(
    'You can still submit your application, but please complete these fields as soon as possible.',
    'Please complete these fields.'
)

# Replace the "Please review your information below. This data was collected from your profile..." message
content = content.replace(
    '<strong>Please review your information below.</strong> This data was collected from your profile.',
    '<strong>Review and edit your application.</strong> Any changes made here apply to this application.'
)


# Remove the bottom form tags and submit sections but KEEP control buttons
content = re.sub(
    r'<div class="alert alert-warning mt-4">.*?</div>\s*<div class="form-check mb-4">.*?</div>',
    '',
    content,
    flags=re.DOTALL
)

# Remove the submit button part
content = re.sub(
    r'<!-- Submit Button -->.*?</button>\s*</div>',
    '',
    content,
    flags=re.DOTALL
)

# We still have "<form method="post">" and "</form>" around the bottom controls because the regex didn't remove them. 
# We should probably remove them too to keep the HTML clean, or just leave them. The JS handles it.
content = content.replace('<form method="post">', '')
content = content.replace('{% csrf_token %}', '') # Removes the extra one, but inline form has one. Wait, inline form has {% csrf_token %}.
content = content.replace('id="inlineEditForm"', 'id="inlineEditForm"\n                    {% csrf_token %}') 


with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacements complete.")
