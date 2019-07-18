function createTab(text: string, id: string|undefined, onClick: (e: MouseEvent) => void) {
    let liElement = document.createElement('li');

    if (id) {
        liElement.id = id;
    }

    let aElement = liElement.appendChild(document.createElement('a'));
    aElement.href = '#';
    aElement.addEventListener(
        'click',
        e => {
            e.preventDefault();
            e.stopPropagation();
            onClick(e);
        },
        { capture: true }
    );
    aElement.appendChild(document.createTextNode(text));

    return liElement;
}

interface TabConfig {
    text: string;
    id?: string;
    onClick: () => void;
}

export function initTabs(tabs: TabConfig[]) {
    let tabsElement = document.querySelector('ul.tab-nav');
    if (!(tabsElement instanceof HTMLUListElement)) {
        console.error('[review] Cannot locate tabs element in DOM');
        return;
    }
    tabsElement.style.position = 'relative';

    let container = document.createElement('div');
    container.style.position = 'absolute';
    container.style.right = '50px';

    for (let tab of tabs) {
        container.appendChild(createTab(tab.text, tab.id, tab.onClick));
    }

    tabsElement.appendChild(container);
}
