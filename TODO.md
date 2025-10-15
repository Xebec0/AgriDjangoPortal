# TODO: Fix Register Modal Issues

## Current Task: Resolve register modal not appearing on click

### Steps:
1. **[COMPLETE]** Edit `templates/modals/register_modal.html`:
   - Split form into 3 steps: Account/Personal (Step 1), Passport/Academic (Step 2), Additional/Documents (Step 3).
   - Add required indicators, error displays, and CSS for steps.
   - Update footer with Previous/Next buttons and step indicator.

2. **[COMPLETE]** Edit `static/js/modal-login-register.js`:
   - Add multi-step logic: showStep, validateStep, handleNext/Prev.
   - Implement client-side validation for required fields and confirmations (email, password, passport).
   - Real-time validation with Bootstrap classes (is-valid/is-invalid).
   - Handle submission on Step 3 via nextBtn.

3. **[COMPLETE]** Test the multi-step modal:
   - Reload the page at http://127.0.0.1:8000/.
   - Click "Register" and verify steps switch on Next/Prev.
   - Test validation: Try advancing without required fields, check confirm matches.
   - Fill form and submit on Step 3 (optional, to verify AJAX).
   - Ensure modal fits screen without overflow.

4. **[COMPLETE]** Confirm original login test:
   - Click "Login" modal, use admin credentials (username: admin, your password).
   - Verify no "no such column: core_profile.address" error and login succeeds.

5. **[COMPLETE]** If all tests pass, mark task complete and clean up TODO.md.
