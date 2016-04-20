import {div, label, input, p, form, span, h2} from '@cycle/dom';
import {Observable} from 'rx';
//import dialog from 'dialog';
//import {dialog} from 'electron';
//const electron = require('electron');

import i_styles from './input.css';
import c_styles from './common.css';
let styles = {};
Object.assign(styles, i_styles, c_styles);


//var remote = require('remote');
//var dialog = remote.require('electron').dialog;
//
//
//

function intent(DOM, id){
    //var path = dialog.showOpenDialog({
    //    properties: ['openDirectory']
    //});
    //dialog.showOpenDialog({ properties: [ 'openDirectory' ]})
    const newValue$ = DOM.select(`#${id}`).events('input').map(ev => ev.target.value);
    const focus$ = DOM.select(`#${id}`).events('focus').map(e => 'focus');
    const blur$ = DOM.select(`#${id}`).events('blur').map(e => 'blur');

    const isFocus$ = focus$.merge(blur$).startWith('blur').map(val => val == 'focus');

    //focus$.map(e => electron.dialog.showOpenDialog({ properties: [ 'openDirectory' ]}) );

    return {newValue$, isFocus$};
}

function model(newValue$, initialValue){

    return newValue$.startWith(initialValue);

}

function view(state$, isFocus$, id, labelName){

    const vtree$ = Observable.combineLatest(state$, isFocus$,

            ( value, focus ) =>

            div({className: styles.group},
                [
                    input({id, required: true, className: styles.input, value}),
                    span({className: styles.bar}),
                    label({for: id, className: ( focus || value ? styles.labelActive : styles.labelInactive)}, labelName),
                ])
            );

    return vtree$;
}


function Input({DOM, props}){

    //const id$ = props$.pluck('id').first();
    //const label$ = props$.pluck('label').first();
    //const initialValue$ = props$
    //  .map(props => (props.initialValue ? props.initialValue : '' ))
    //  .first();
    const {id, labelName} = props;
    const initialValue = props.initialValue ? props.initialValue : '';

    const {newValue$, isFocus$} = intent(DOM, id);
    const state$ = model(newValue$, initialValue);
    const vtree$ = view(state$, isFocus$, id, labelName);


  return {
      vtree$,
      value$: state$,
      id
  }


}

export default Input;
