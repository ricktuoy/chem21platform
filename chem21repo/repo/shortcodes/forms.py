from django import forms


class FigureGroupForm(forms.Form):
    media = forms.MultipleChoiceField(
        label="Image(s)",
        choices=[])  # choices are defined on init
    figure_type = forms.CharField(
        label="Type of figure",
        help_text="e.g. Figure/Scheme/Table (defaults to Figure)",
        required=False)
    caption = forms.CharField(
        label="Caption",
        max_length=200,
        required=False)
    layout = forms.ChoiceField(
        label="Layout",
        choices=[
            ("full_width", "Full width"),
            ("aside", "Inset (40% width"),
            ("stacked2", "Side-by-side (pair)")],
        initial="full_width")

    def __init__(self, question, *args, **kwargs):
        super(FigureGroupForm, self).__init__(*args, **kwargs)
        self.fields['media'].choices = [
            (f.pk, f.title) for f in question.files.filter(type="image")]


class TableForm(forms.Form):
    inner_html = forms.TextField(

        )
    caption = forms.CharField(
        label="Caption",
        max_length=200,
        required=False)
