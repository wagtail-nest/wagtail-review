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

declare let window: any;

document.addEventListener('DOMContentLoaded', () => {
    const shareStore = createStore(shareReducer);
    const commentsStore = createStore(commentsReducer);
    const api = new APIClient(
        window.wagtailPageId /* Injected by GuacamoleMenuItem in review/wagtail_hooks.py */
    );

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
        if (e.key === 'Escape') {
            shareStore.dispatch(hideShareModal());
            commentsStore.dispatch(hideComments());
        }
    });

    // Load initial shares
    api.getShares().then(shares => {
        for (const share of shares) {
            shareStore.dispatch(putShare(Share.fromApi(share)));
        }
    });

    // Load initial commebts
    api.getComments().then(comments => {
        commentsStore.dispatch(loadComments(comments.map(Comment.fromApi)));
    });

    // Render share UI
    const shareContainer = document.createElement('div');
    document.body.append(shareContainer);

    const renderShare = () => {
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
    const commentsButton = document.getElementById('comments-button');
    if (commentsButton instanceof HTMLElement) {
        const commentsContainer = document.createElement('div');
        commentsButton.append(commentsContainer);

        commentsContainer.style.position = 'relative';

        const commentsButtonATag = commentsButton.querySelector('a');

        const renderComments = () => {
            const state = commentsStore.getState();
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
                const numUnresolvedComments = state.comments.filter(comment => !comment.isResolved).length;

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
