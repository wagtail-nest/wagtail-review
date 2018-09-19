$(function() {
    $('input[name="action-submit-for-review"],button[name="action-submit-for-review"]').click(function() {
        ModalWorkflow({
            url: '/admin/wagtail_review/create_review/',
        });
        return false;
    });
});
