$(function() {
    $('input[name="action-submit-for-review"],button[name="action-submit-for-review"]').click(function() {
        var createReviewUrl = $(this).data('url');
        ModalWorkflow({
            url: createReviewUrl,
            onload: {
                'form': function(modal, jsonData) {
                    var autocompleteField = $('#id_create_review-reviewer_autocomplete', modal.body);
                    var autocompleteUrl = autocompleteField.data('autocomplete-url');
                    autocompleteField.autocomplete({
                        'minLength': 2,
                        'source': function(request, response) {
                            $.getJSON(autocompleteUrl, {'q': request.term}, function(jsonResponse) {
                                var results = [];
                                for (var i = 0; i < jsonResponse.results.length; i++) {
                                    results[i] = {
                                        'value': jsonResponse.results[i]['id'],
                                        'label': jsonResponse.results[i]['full_name']
                                    };
                                }
                                response(results);
                            });
                        },
                        'focus': function( event, ui ) {
                            /* prevent populating the input box with the ID */
                            return false;
                        },
                        'select': function(event, ui) {
                            console.log('selected user ID: ' + ui.item.value);
                            autocompleteField.val('');
                            return false;
                        }
                    });
                }
            }
        });
        return false;
    });
});
