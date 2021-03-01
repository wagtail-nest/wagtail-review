(function() {
    function renderWithUsername(annotation) {
        if (annotation.text) {
            var author = '<p style="font-weight: bold;">' + annotator.util.escapeHtml(annotation.user.name) + '</p>'
            return author + annotator.util.escapeHtml(annotation.text);
        } else {
            return "<i>" + _t('No comment') + "</i>";
        }
    }

    window.annotatorExt = {
        'viewerWithUsernames': function(viewer) {
            viewer.setRenderer(renderWithUsername);
        },
        'viewerModeUi': function() {
            /* Read-only view of annotations. Taken from https://github.com/openannotation/annotator/issues/580#issuecomment-254772752 */
            var element = document.body; // Or whatever is your selector/element when you initialize the annotator
            var ui = {};

            return {
                start: function () {
                    ui.highlighter = new annotator.ui.highlighter.Highlighter(element);
                    ui.viewer = new annotator.ui.viewer.Viewer({
                        permitEdit: function (ann) { return false; },
                        permitDelete: function (ann) { return false; },
                        autoViewHighlights: element
                    });
                    ui.viewer.setRenderer(renderWithUsername);
                    ui.viewer.attach();
                },
                destroy: function () {
                    ui.highlighter.destroy();
                    ui.viewer.destroy();
                },
                annotationsLoaded: function (anns) {
                    ui.highlighter.drawAll(anns);
                }
            };
        }
    };
})();
