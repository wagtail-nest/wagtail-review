import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { createStore } from 'redux';

import ShareModal from './components/ShareModal';
import Comments from './components/Comments';
import APIClient from './api';
import { reducer as shareReducer, Share } from './state/share';
import { Comment, reducer as commentsReducer } from './state/comments';
import { initTabs } from './utils/tabs';
import { showShareModal, hideShareModal, putShare } from './actions/share';
import { showComments, loadComments, hideComments } from './actions/comments';

declare var window: any;

document.addEventListener('DOMContentLoaded', () => {
    initTabs([
        {
            text: 'Share',
            onClick() {
                shareStore.dispatch(showShareModal());
            }
        },
        {
            text: 'Comments',
            id: 'comments-button',
            onClick() {
                if (commentsStore.getState().isOpen) {
                    commentsStore.dispatch(hideComments());
                } else {
                    commentsStore.dispatch(showComments());
                }
            }
        }
    ]);

    document.addEventListener('keydown', (e: KeyboardEvent) => {
        // Close share modal and comments when esc is pressed
        if (e.key == 'Escape') {
            shareStore.dispatch(hideShareModal());
            commentsStore.dispatch(hideComments());
        }
    });

    let shareStore = createStore(shareReducer);
    let commentsStore = createStore(commentsReducer);
    let api = new APIClient(
        window.wagtailPageId /* Injected by GuacamoleMenuItem in review/wagtail_hooks.py */
    );

    // Load initial shares
    api.getShares().then(shares => {
        for (let share of shares) {
            shareStore.dispatch(putShare(Share.fromApi(share)));
        }
    });

    // Load initial commebts
    api.getComments().then(comments => {
        commentsStore.dispatch(loadComments(comments.map(Comment.fromApi)));
    });

    // Render share UI
    let shareContainer = document.createElement('div');
    document.body.append(shareContainer);

    let renderShare = () => {
        ReactDOM.render(
            <ShareModal
                api={api}
                store={shareStore}
                {...shareStore.getState()}
            />,
            shareContainer
        );
    };

    renderShare();
    shareStore.subscribe(renderShare);

    // Render comments UI
    let commentsButton = document.getElementById('comments-button');
    if (commentsButton instanceof HTMLElement) {
        let commentsContainer = document.createElement('div');
        commentsButton.append(commentsContainer);

        commentsContainer.style.position = 'relative';

        let commentsButtonATag = commentsButton.querySelector('a');

        let renderComments = () => {
            let state = commentsStore.getState();
            ReactDOM.render(
                <Comments
                    api={api}
                    store={commentsStore}
                    {...state}
                />,
                commentsContainer
            );

            // Update number displayed on comments tab
            if (commentsButtonATag instanceof HTMLElement) {
                let numUnresolvedComments = state.comments.filter(comment => !comment.isResolved).length;

                if (numUnresolvedComments > 0) {
                    commentsButtonATag.classList.add('errors');
                    commentsButtonATag.dataset.count = numUnresolvedComments.toString();
                } else {
                    commentsButtonATag.classList.remove('errors');
                }
            }
        };

        renderComments();
        commentsStore.subscribe(renderComments);
    }
});
