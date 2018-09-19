$(function() {
    $('input[name="action-submit-for-review"],button[name="action-submit-for-review"]').click(function() {
        var createReviewUrl = $(this).data('url');
        ModalWorkflow({
            url: createReviewUrl,
        });
        return false;
    });
});
