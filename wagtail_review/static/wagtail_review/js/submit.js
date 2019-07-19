$(function() {

    function createReviewOnload(modal, jsonData) {
        /* onload behaviours for the create review form */

        var reviewerList = $('#id_create_review-reviewer_form_container');
        var totalFormsInput = $('#id_create_review_assignees-TOTAL_FORMS');
        var formCount = parseInt(totalFormsInput.val(), 10);
        var emptyFormTemplate = document.getElementById('id_create_review_assignees-EMPTY_FORM_TEMPLATE');
        if (emptyFormTemplate.innerText) {
            emptyFormTemplate = emptyFormTemplate.innerText;
        } else if (emptyFormTemplate.textContent) {
            emptyFormTemplate = emptyFormTemplate.textContent;
        }

        function initReviewerDeleteLink(li, formIndex) {
            $('#id_create_review_assignees-' + formIndex + '-delete_link').click(function() {
                $('#id_create_review_assignees-' + formIndex + '-DELETE').val('1');
                li.fadeOut('fast');
                return false;
            });
        }

        function addReviewer(id, email, label) {
            var newFormHtml = $(emptyFormTemplate
                .replace(/__prefix__/g, formCount)
                .replace(/<-(-*)\/script>/g, '<$1/script>'));
            reviewerList.append(newFormHtml);
            $('#id_create_review_assignees-' + formCount + '-user').val(id);
            $('#id_create_review_assignees-' + formCount + '-email').val(email);
            $('#id_create_review_assignees-' + formCount + '-label').text(label);
            initReviewerDeleteLink(newFormHtml, formCount);

            formCount++;
            totalFormsInput.val(formCount);
        }

        var autocompleteField = $('#id_create_review-reviewer_autocomplete', modal.body);

        var autocompleteErrorMessage = $('<p class="error-message"><span>Please enter an email address, or select a user from the dropdown</span></p>');
        autocompleteField.closest('.field-content').append(autocompleteErrorMessage);
        autocompleteErrorMessage.hide();

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
                addReviewer(ui.item.value, null, ui.item.label);
                autocompleteField.val('');
                autocompleteErrorMessage.hide();
                return false;
            }
        });

        function addReviewerIfEmail() {
            /* add the value of autocompleteField to the reviewer list if it looks like an email address */
            var val = autocompleteField.val();
            if (/^[^\@]+\@[^\@]+\.[^\@]+$/.test(val)) {
                addReviewer(null, val, val);
                autocompleteField.val('');
                autocompleteErrorMessage.hide();
            } else {
                autocompleteErrorMessage.show();
            }
        }
        $('#id_create_review-reviewer_autocomplete_add', modal.body).click(addReviewerIfEmail);
        autocompleteField.keypress(function(e) {
            if (e.keyCode == 13) {
                addReviewerIfEmail();
                return false;
            }
        });

        $('form', modal.body).on('submit', function() {
            modal.postForm(this.action, $(this).serialize());
            return false;
        });

    }

    function onValidateOK(modal, jsonData) {
        /* transfer create-review form contents to the real page-edit form */
        var formFields = $('form', modal.body).serializeArray();
        var editForm = $('form#page-edit-form');
        for (var i = 0; i < formFields.length; i++) {
            var input = $('<input type="hidden">').attr({
                'name': formFields[i].name, 'value': formFields[i].value
            });
            editForm.append(input);
        }
        /* Add a hidden field to substitute for clicking the 'submit for review' button,
        so that we know this was a submit-for-review action when intercepting the form post */
        editForm.append('<input type="hidden" name="action-submit-for-review" value="1">');
        editForm.submit();
    }

    /* behaviour for the submit-for-review menu item */
    $('input[name="action-submit-for-review"],button[name="action-submit-for-review"]').click(function() {
        var createReviewUrl = $(this).data('url');
        ModalWorkflow({
            url: createReviewUrl,
            onload: {
                'form': createReviewOnload,
                'done': onValidateOK
            }
        });
        return false;
    });
});
