import re
import os

file_path = r'c:\Users\Arvin\Documents\AgriDjangoPortal\templates\candidate_apply_edit.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace CSS
old_css_start = "    .info-section {"
old_css_end = "        .edit-mode .info-row {\n            background-color: #ffffff;\n        }\n    }"
if old_css_start in content and old_css_end in content:
    start_idx = content.find(old_css_start)
    end_idx = content.find(old_css_end) + len(old_css_end)
    old_css = content[start_idx:end_idx]

    new_css = """    /* Mobile-first: base = 320px+ */
    .info-section {
        border-bottom: 1px solid #eee;
        padding-bottom: 1.25rem;
        margin-bottom: 1.25rem;
    }
    
    .info-section:last-child {
        border-bottom: none;
    }
    
    .info-section-title {
        margin-bottom: 1rem;
        color: #0275d8;
        font-weight: 600;
        border-bottom: 2px solid #e7f1ff;
        padding-bottom: 0.5rem;
    }
    
    /* Mobile: single column grid */
    .info-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0;
    }
    
    .grid-full-width {
        grid-column: span 1;
    }
    
    /* Mobile: stack label above value */
    .info-row {
        display: flex;
        flex-direction: column;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f8f9fa;
        align-items: stretch;
        gap: 0.15rem;
    }
    
    .info-label {
        font-weight: 600;
        min-width: 0;
        color: #495057;
        font-size: 0.85rem;
    }
    
    .info-value {
        flex: 1;
        color: #212529;
        font-size: 0.95rem;
    }
    
    .missing-info {
        color: #dc3545;
        font-style: italic;
    }

    /* Tablets (768px+) — side-by-side layout */
    @media (min-width: 768px) {
        .info-row {
            flex-direction: row;
            align-items: flex-start;
            gap: 0;
        }

        .info-label {
            min-width: 160px;
            font-size: 0.95rem;
        }
    }

    /* Desktop (992px+) — 2-column grid */
    @media (min-width: 992px) {
        .info-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0 2.5rem;
        }

        .grid-full-width {
            grid-column: span 2;
        }
    }
    
    .program-card {
        background: linear-gradient(135deg, #2c3e50 0%, #000000 100%);
        color: white;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1.5rem;
    }

    @media (min-width: 768px) {
        .program-card {
            padding: 1.5rem 2rem;
        }
    }

    /* ── Crossfade animations (matching profile edit transition) ── */
    @keyframes editFadeSlideIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    @keyframes editRowHighlight {
        from { background-color: transparent; }
        to   { background-color: #ffffff; }
    }

    @keyframes editBtnFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* --- Read → Edit transition --- */
    .edit-mode .display-value {
        display: none !important;
    }

    .edit-mode .edit-input {
        display: block !important;
        animation: editFadeSlideIn 0.32s ease forwards;
    }

    .edit-mode .info-row {
        border-radius: 4px;
        animation: editRowHighlight 0.35s ease forwards;
    }

    .edit-mode .info-section {
        animation: editFadeSlideIn 0.35s ease forwards;
    }

    /* Stagger sections for cascading effect */
    .edit-mode .info-section:nth-child(1) { animation-delay: 0s; }
    .edit-mode .info-section:nth-child(2) { animation-delay: 0.06s; }
    .edit-mode .info-section:nth-child(3) { animation-delay: 0.12s; }
    .edit-mode .info-section:nth-child(4) { animation-delay: 0.18s; }
    .edit-mode .info-section:nth-child(5) { animation-delay: 0.24s; }
    .edit-mode .info-section:nth-child(6) { animation-delay: 0.30s; }

    /* --- Button swap --- */
    .save-controls {
        display: none;
    }

    .edit-mode .save-controls {
        display: flex !important;
        animation: editBtnFadeIn 0.3s ease 0.1s both;
    }

    .edit-mode .edit-controls {
        display: none !important;
    }

    /* --- Reduced motion --- */
    @media (prefers-reduced-motion: reduce) {
        .edit-mode .edit-input,
        .edit-mode .info-row,
        .edit-mode .info-section,
        .edit-mode .save-controls {
            animation: none !important;
        }
        .edit-mode .info-row {
            background-color: #ffffff;
        }
    }"""
    content = content.replace(old_css, new_css)
else:
    print("CSS block not found!")

# Replace program-card
old_card = '''    <div class="program-card shadow">
        <h3 class="mb-3"><i class="fas fa-seedling me-2"></i>{{ candidate.program.title }}</h3>
        <p class="mb-2"><i class="fas fa-map-marker-alt me-2"></i><strong>Location:</strong> {{ candidate.program.location }}</p>
        <p class="mb-2"><i class="fas fa-calendar-alt me-2"></i><strong>Start Date:</strong> {{ candidate.program.start_date|date:"F d, Y" }}</p>
        <p class="mb-0"><i class="fas fa-users me-2"></i><strong>Available Slots:</strong> {{ candidate.program.capacity }}</p>
    </div>'''

new_card = '''    <div class="program-card shadow">
        <h3 class="h4 mb-3"><i class="fas fa-seedling me-2 text-success"></i>{{ candidate.program.title }}</h3>
        <div class="d-flex flex-wrap gap-x-4 gap-y-2 text-light">
            <div class="me-4"><i class="fas fa-map-marker-alt me-2"></i><strong>Location:</strong> {{ candidate.program.location }}</div>
            <div class="me-4"><i class="fas fa-calendar-alt me-2"></i><strong>Start Date:</strong> {{ candidate.program.start_date|date:"F d, Y" }}</div>
            <div><i class="fas fa-users me-2"></i><strong>Available Slots:</strong> {{ candidate.program.capacity }}</div>
        </div>
    </div>'''

if old_card in content:
    content = content.replace(old_card, new_card)

# Inject <div class="info-grid"> ... </div> into .info-section
# Find each section by <div class="info-section">
# Then find the first </h4> (end of title) and insert <div class="info-grid">
# Then find the matching </div> for <div class="info-section">... but it's easier:
# Since all info-rows are inside <div class="info-section">, we can just replace
# '<div class="info-section">' with a marker, process each, etc.

# Actually, we can use a simpler approach:
# Split by '<div class="info-section">'
parts = content.split('<div class="info-section">')
new_parts = [parts[0]]

for part in parts[1:]:
    # Find the title end
    h4_end = part.find('</h4>')
    if h4_end != -1:
        # Check if already wrapped
        if '<div class="info-grid">' not in part:
            h4_end += 5 # past </h4>
            head = part[:h4_end]
            body = part[h4_end:]
            
            # The body ends with something. Let's find the last '</div>\n                '
            # before the next major tag.
            # Usually each section in this file is followed by:
            # </div>
            # 
            # <!-- Passport Information Section -->
            
            # Find the last closing div of the section that's at the same indentation
            # It's usually '                </div>\n                \n                <!-- '
            # Or at the end of the form.
            # We can find all info-row items, and put <div class="info-grid"> before the first one
            # and </div> after the last one.
            
            first_info_row = body.find('<div class="info-row">')
            if first_info_row == -1:
                first_info_row = body.find('<div class="info-row grid-full-width">')
            
            if first_info_row != -1:
                # Find the end of the last info-row.
                # Actually, let's just insert '<div class="info-grid">' after </h4>
                # and '</div> <!-- end info-grid -->' right before the last closing </div> in `part` 
                # (which closes the info-section)
                # Let's find the last </div> in the string `body`.
                last_div_idx = body.rfind('</div>')
                if last_div_idx != -1:
                    new_body = (
                        body[:first_info_row] + 
                        '                    <div class="info-grid">\n                    ' +
                        body[first_info_row:last_div_idx] +
                        '                    </div> <!-- end info-grid -->\n                ' +
                        body[last_div_idx:]
                    )
                    part = head + new_body
    new_parts.append(part)

content = '<div class="info-section">'.join(new_parts)

# Fix full-width fields
full_width_labels = [
    'Address:',
    'Parents:',
    'University:',
    'Job Experience Details:',
    'Remarks / Special Conditions:'
]

for label in full_width_labels:
    # Use regex to replace '<div class="info-row">\s*<div class="info-label">Address:</div>'
    # with '<div class="info-row grid-full-width">'
    pattern = r'<div class="info-row">(\s*<div class="info-label">' + re.escape(label) + r'</div>)'
    replacement = r'<div class="info-row grid-full-width">\1'
    content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done successfully!")
