import * as React from 'react';
import * as dateFormat from 'dateformat';

import PageAPIClient from '../../api/page';
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
            <p className="comment__text">{comment.text}</p>

            <p className="comment__info">
                {comment.author.name} - {dateFormat(comment.date, 'h:MM mmmm d')}
            </p>
            <div className="comment__resolved">
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
            <a
                href={comment.frontendUrl}
                onClick={onClickLink}
                className="comment__view-on-frontend"
                target="_blank"
                rel="noopener noreferrer"
            >
                View on frontend
            </a>
        </li>
    );
}

interface CommentsProps extends State {
    api: PageAPIClient;
    store: Store;
}

export default function Comments(props: CommentsProps) {
    const { isOpen, showResolvedComments, store } = props;
    let { comments } = props;

    if (!isOpen) {
        return <div />;
    }

    let showHideResolvedCommentsInput = <></>;
    const numResolvedComments = comments.filter(comment => comment.isResolved)
        .length;

    if (numResolvedComments > 0) {
        const onChangeShowHideResolvedComments = (
            e: React.ChangeEvent<HTMLInputElement>
        ) => {
            store.dispatch(showHideResolvedComments(e.target.checked));
        };

        showHideResolvedCommentsInput = (
            <div className="comments__show-hide-resolved">
                Show {numResolvedComments} resolved comments
                <input
                    type="checkbox"
                    onChange={onChangeShowHideResolvedComments}
                    checked={showResolvedComments}
                />
            </div>
        );

        if (!showResolvedComments) {
            comments = comments.filter(comment => !comment.isResolved);
        }
    }

    const commentsRendered = comments.map(renderComment);

    return (
        <div className="comments">
            {showHideResolvedCommentsInput}
            <ul>{commentsRendered}</ul>
        </div>
    );
}
