import * as React from 'react';
import * as Modal from 'react-modal';

import './style.scss';

interface Props extends Modal.Props {
    onClickCloseButton?(): void;
}

export default class WagtailReactModal extends React.Component<Props> {
    componentDidMount() {
        Modal.setAppElement('div.wrapper');
    }

    render() {
        const onClickClose = (e: React.MouseEvent) => {
            e.preventDefault();

            const { onClickCloseButton } = this.props;

            if (onClickCloseButton) {
                onClickCloseButton();
            }
        };

        const defaultProps = {
            className: 'react-modal__dialog',
            overlayClassName: 'react-modal'
        };

        const props: Modal.Props = Object.assign(defaultProps, this.props);

        const oldOnAfterOpen = props.onAfterOpen;
        props.onAfterOpen = () => {
            const backdrop = document.body.appendChild(
                document.createElement('div')
            );
            backdrop.classList.add('js-wagtail-react-modal-backdrop');
            backdrop.classList.add('modal-backdrop');
            backdrop.classList.add('in');

            if (oldOnAfterOpen) {
                oldOnAfterOpen();
            }
        };

        const oldOnAfterClose = props.onAfterClose;
        props.onAfterClose = () => {
            const backdrop = document.querySelector(
                'body > div.js-wagtail-react-modal-backdrop'
            );

            if (backdrop instanceof HTMLElement) {
                backdrop.remove();
            }

            if (oldOnAfterClose) {
                oldOnAfterClose();
            }
        };

        const { contentLabel, children } = this.props;

        return (
            <Modal {...props}>
                <div className="react-modal__content">
                    <button
                        type="button"
                        className="button close icon text-replace icon-cross"
                        data-dismiss="modal"
                        aria-hidden="true"
                        onClick={onClickClose}
                    >
                        ×
                    </button>
                    <div className="react-modal__body">
                        <header className="merged tab-merged">
                            <div className="row nice-padding">
                                <div className="left">
                                    <div className="col header-title">
                                        <h1 className="icon icon-share">
                                            {contentLabel}
                                        </h1>
                                    </div>
                                </div>
                            </div>
                        </header>

                        <div className="tab-content">{children}</div>
                    </div>
                </div>
            </Modal>
        );
    }
}
