var annotatorExt = {
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
    },
    'setCredentials': function(options) {
        return {
            beforeAnnotationCreated: function (ann) {
                for (var key in options.credentials) {
                    ann[key] = options.credentials[key];
                }
            }
        };
    }
};
