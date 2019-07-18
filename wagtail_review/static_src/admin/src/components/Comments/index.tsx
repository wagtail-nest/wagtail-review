import * as React from 'react';
import * as dateFormat from 'dateformat';

import APIClient from '../../api';
import { Comment, Store, State } from '../../state/comments';

import './style.scss';
import { showHideResolvedComments } from '../../actions/comments';

function renderComment(comment: Comment): React.ReactFragment {
    const onClickLink = (e: React.MouseEvent<HTMLAnchorElement>) => {
        e.preventDefault();
        if (e.target instanceof HTMLAnchorElement) {
            window.open(e.target.href, '_blank');
        }
    };

    return (
        <li key={comment.id} className="comment">
            <div className="comment__header">
                <div className="comment__header-info">
                    <h2>{comment.author.name}</h2>
                    <p className="comment__date">
                        {dateFormat(comment.date, 'h:MM mmmm d')}
                    </p>
                </div>
                <div className="comment__header-resolved">
                    <label>
                        Resolved
                        <input
                            name="resolved"
                            type="checkbox"
                            checked={comment.isResolved}
                            disabled
                        />
                    </label>
                </div>
            </div>
            <p className="comment__text">{comment.text}</p>
            <a href={comment.frontendUrl} onClick={onClickLink} className="comment__view-on-frontend" target="_blank" rel="noopener noreferrer">View on frontend</a>
        </li>
    );
}

interface CommentsProps extends State {
    api: APIClient;
    store: Store;
}

export default function Comments(props: CommentsProps) {
    const { isOpen, showResolvedComments, store } = props;
    let { comments } = props;

    if (!isOpen) {
        return <div />;
    }

    let showHideResolvedCommentsInput = <></>;
    const numResolvedComments = comments.filter(comment => comment.isResolved).length;

    if (numResolvedComments > 0) {
        const onChangeShowHideResolvedComments = (e: React.ChangeEvent<HTMLInputElement>) => {
            store.dispatch(
                showHideResolvedComments(e.target.checked)
            );
        };

        showHideResolvedCommentsInput = <div className="comments__show-hide-resolved">
            Show {numResolvedComments} resolved comments
            <input type="checkbox"
                onChange={onChangeShowHideResolvedComments}
                checked={showResolvedComments}
            />
        </div>;

        if (!showResolvedComments) {
            comments = comments.filter(comment => !comment.isResolved);
        }
    }

    const commentsRendered = comments.map(renderComment);

    return (
        <div className="comments">
            {showHideResolvedCommentsInput}
            <ul>
                {commentsRendered}
            </ul>
        </div>
    );
}
