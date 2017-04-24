LMS_PAGE_MENU = [
    ('Text', [
        'edit',
        'load'
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
        'add',
    ])]
