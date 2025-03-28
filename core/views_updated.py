"""
Instructions for updating the program_register view in core/views.py:

Find the program_register view function (around line 274) and update it to add 
notifications for admin users when a user registers for a program.

The updated function should look like this:
"""

@login_required
def program_register(request, program_id):
    """Register for a program"""
    program = get_object_or_404(AgricultureProgram, id=program_id)
    
    # Check if already registered
    try:
        Registration.objects.get(user=request.user, program=program)
        messages.warning(request, 'You are already registered for this program.')
        return redirect('program_detail', program_id=program_id)
    except Registration.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = ProgramRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.user = request.user
            registration.program = program
            registration.save()
            
            # Create notification for the registering user
            Notification.add_notification(
                request.user,
                f'You have successfully registered for {program.title}.',
                Notification.SUCCESS,
                f'/programs/{program.id}/'
            )
            
            # Create notifications for all admin users
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.add_notification(
                    admin,
                    f'New registration: {request.user.get_full_name() or request.user.username} has registered for {program.title}.',
                    Notification.INFO,
                    f'/programs/{program.id}/registrants/'
                )
            
            messages.success(request, f'Successfully registered for {program.title}!')
            return redirect('profile')
    else:
        form = ProgramRegistrationForm()
    
    return render(request, 'program_register.html', {'form': form, 'program': program}) 