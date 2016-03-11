
import Cycle from '@cycle/core';
import {makeDOMDriver, div, label, input, p, form, span} from '@cycle/dom';

import styles from './index.css';


//import {restart, restartable} from 'cycle-restart';

function main(drivers) {
  return {
    //DOM: drivers.DOM.select('input').events('click')
    //  .map(ev => ev.target.checked)
    //  .startWith(false)
    //  .map(toggled =>
    //    div([
    //      input({type: 'checkbox'}), 'Toggle me',
    //      p(toggled ? 'ON' : 'off')
    //    ])
    //  )



    //DOM: Rx.Observable.just(
    //    form(
    //      div('.mdl-textfield.mdl-js-textfield.mdl-textfield--floating-label',
    //        [
    //        input('#name.mdl-textfield__input'), label({forHtml: 'name', className: 'mdl-textfield__label'}, 'User name'),
    //        //input({id: 'email'}), label({for: 'email'}, 'User email'),
    //    ] )))

    DOM: Rx.Observable.just(

        div({className: styles.container}, [
            form(
              div({className: styles.group},
                [
                input({id: 'name', required: true, className: styles.input}),
                span({className: styles.bar}),
                label({for: 'name', className: styles.label}, 'User name'),
            ] ))
        ])

    )


  };
}

const drivers = {
  DOM: makeDOMDriver('#app')
  //DOM: restartable(makeDOMDriver('#app'))
};

Cycle.run(main, drivers);

//if (module.hot) {
//  module.hot.accept('./src/app', () => {
//    app = require('./src/app').default;
//
//    restart(app, drivers, {sinks, sources});
//  });
//}
