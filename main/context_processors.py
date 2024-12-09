def navbar_context(request):
    """Add navbar-related context data to all templates."""
    return {
        'navbar_attributes': {
            'foto_url': request.session.get('foto_url', ''),
            'user_name': request.session.get('user_name', ''),
            'user_type': request.session.get('user_type', ''),
            'is_authenticated': request.session.get('is_authenticated', False),
        }
    }
