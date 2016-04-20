
import {Observable} from 'rx';
import Cycle from '@cycle/core';
import {makeDOMDriver, select, option, div, span, input, ul, li, label} from '@cycle/dom';
//import styles from './select.css';


import c_styles from './common.css';
import s_styles from './select.css';
let styles = {};
Object.assign(styles, c_styles, s_styles);



function intent({DOM, props$}){
    const initialValue$ = props$.pluck('initial');
    const clickOption$ = DOM.select('li').events('click');
    //const clickEv$ = DOM.events('click');
    //const blur$ = DOM.select('#input').events('blur').map(e => 'true');
    return {
        toggleSelect$: DOM.select('#input').events('click').merge(clickOption$),
        selectOption$: initialValue$.concat(clickOption$.pluck('target', 'textContent')),
    }

}

function model(actions, props$){
    return Observable.combineLatest(actions.toggleSelect$.startWith(false).scan(val => !val),
                                    actions.selectOption$,
                                    props$.pluck('options'),
                                    props$.pluck('labelName'),
                                    (showOptions, selectedOption, options, labelName) => {return {showOptions, selectedOption, options, labelName}});
}

function view(state$){
    return state$.map(({showOptions, selectedOption, options, labelName}) =>
      div({className: styles.input_field}, [
        div({className: styles.select_wrapper}, [
            span({className: styles.caret}, '▼'),
            input({id: 'input' ,className: styles.input /*select_dropdown*/, readOnly: true, type: 'text', value: `${selectedOption}`}),
            span({className: styles.bar}),
            (!showOptions ? null : // nulls are just ignored by hyperscript
            ul({className: styles.dropdownContent, },
               options.map(option => li({className: (option == selectedOption? styles.dropLiActive:styles.dropLi)},
                                        [span({className: styles.dropLiSpan}, option) ] ))
            ))
        ]),
        label({className: styles.labelActive}, labelName)
      ])
      );

}


function Select(sources) {

  //const props$ = sources.props$;
  ////const vtree$ = props$.map((vals) => {
  ////      return select(
  ////          vals.map( val => option({value: val}, `Option ${val}`) )
  ////      )}
  ////      );


  ////const initialValue$ = props$.map(vals => vals[0]).first();
  ////const value$ = initialValue$.concat(
  ////  sources.DOM.select('select').events('input').map(ev => ev.target.value));
  ////const vtree$ = Observable.just(createSelect());
  //const vtree$ = createSelect2(sources.DOM);


  const actions = intent(sources);
  const state$ = model(actions, sources.props$);
  const vtree$ = view(state$);

  return {
      vtree$,
      value$: actions.selectOption$,
  }
}

export default Select;
