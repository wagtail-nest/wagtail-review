$(function() {
    $('input[name="action-submit-for-review"],button[name="action-submit-for-review"]').click(function() {
        ModalWorkflow({
            url: window.chooserUrls.imageChooser,
        });
        return false;
    });
});
