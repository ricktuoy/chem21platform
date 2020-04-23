LMS_PAGE_MENU = [
    ('Page', [
        ('new', {
            'display_name': 'Add child page',
            'id_type': 'struct',
            'param_type': 'querystring'
        }),
        ('edit', {
            'view_name': "admin:repo_question_change",
            'display_name': 'Edit text',
        })
    ]),
    ('Figure', [
        ('add', {
            'params': ['para', 'fig'],
            'instruction': 'Click a location below to insert a figure.'}),
        ('remove', {
            'params': ['para', 'fig'],
            'instruction': 'Click a figure below to edit it.'}),
        ('edit', {
            'params': ['para', 'fig'],
            'instruction': 'Click a figure below to remove it from the page.'})
    ]),
    ('Video', [
        'edit',
    ]),
    ('Quiz', [
        'edit',
    ]),
    ('References', [
        ('add', {
            'display_name': "Upload .bib",
            'id_type': None
        }),
    ])]
