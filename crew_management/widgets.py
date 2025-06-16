# crew_management/widgets.py

from django import forms
from django.forms.utils import flatatt
from django.utils.html import format_html
import json

class SsbCdcNumbersWidget(forms.TextInput): # Inherit from TextInput, but we'll render more complex HTML
    template_name = 'crew_management/widgets/ssb_cdc_numbers_widget.html'

    def render(self, name, value, attrs=None, renderer=None):
        # Value might be a JSON list or None/empty string
        if value is None:
            value = '[]' # Default to empty JSON array string

        # Ensure value is a stringified JSON array
        if not isinstance(value, str):
            value = json.dumps(value)

        # The hidden input will hold the actual JSON string
        final_attrs = self.build_attrs(self.attrs, attrs)
        hidden_input_html = format_html('<input type="hidden" name="{}" value="{}"{}>', name, value, flatatt(final_attrs))

        # Pass context to the template
        context = {
            'widget': {
                'name': name,
                'value': value, # The JSON string to be parsed by JS
                'attrs': self.build_attrs(self.attrs, attrs),
            },
            'hidden_input_html': hidden_input_html, # The actual Django form input
        }
        return self._render(self.template_name, context, renderer)

    # This method is crucial for handling incoming data from the HTML form.
    # The JS will update the hidden input, and Django will read that.
    def value_from_datadict(self, data, files, name):
        # The JavaScript in the template will update the hidden input field named 'name'
        # with the JSON string representing all the SSB/CDC numbers.
        json_string = data.get(name)
        if json_string:
            try:
                # Attempt to parse the JSON string back into a Python object (list of dicts)
                return json.loads(json_string)
            except json.JSONDecodeError:
                # If invalid JSON, return the raw string so form validation can catch it
                return json_string
        return None # Return None if no data or empty string