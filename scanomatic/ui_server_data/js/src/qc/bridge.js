// @flow

import {
    retrievePlateCurves, setProject, setPlate, focusCurve,
    setQualityIndexQueue, nextQualityIndex, previousQualityIndex, setQualityIndex,
} from './actions';
import {
    getRawCurve, getSmoothCurve, getTimes, getPlate, getFocus, getCurrrentQIndexInfo,
} from './selectors';

import type { Action, ThunkAction } from './actions';
import type {
    State, TimeSeries, PlatePosition, QualityIndexInfo, QualityIndexQueue,
} from './state';

type Store = {
    +dispatch: (Action | ThunkAction) => any,
    +getState: () => State,
    +subscribe: (() => any) => any,
}

class Selectors {
    store : Store

    constructor(store : Store) {
        this.store = store;
    }

    getRawCurve(plate: number, row : number, col : number) : ?TimeSeries {
        const state = this.store.getState();
        return getRawCurve(state, plate, row, col);
    }

    getSmoothCurve(plate: number, row : number, col : number) : ?TimeSeries {
        const state = this.store.getState();
        return getSmoothCurve(state, plate, row, col);
    }

    getTimes(plate: number) : ?TimeSeries {
        const state = this.store.getState();
        return getTimes(state, plate);
    }

    getPlate() : ?number {
        const state = this.store.getState();
        return getPlate(state);
    }

    getFocus() : ?PlatePosition {
        const state = this.store.getState();
        return getFocus(state);
    }

    getCurrrentQIndexInfo(plate: number) : ?QualityIndexInfo {
        const state = this.store.getState();
        return getCurrrentQIndexInfo(state, plate);
    }
}

class Actions {
    store: Store;

    constructor(store : Store) {
        this.store = store;
    }

    setProject(project: string) {
        this.store.dispatch(setProject(project));
    }

    setPlate(plate: number) {
        this.store.dispatch(setPlate(plate));
    }

    setFocus(plate: number, row: number, col: number) {
        this.store.dispatch(focusCurve(plate, row, col));
    }

    setQualityIndexQueue(plate: number, queue: QualityIndexQueue) {
        this.store.dispatch(setQualityIndexQueue(plate, queue));
    }

    setQualityIndex(plate: number, index: number) {
        this.store.dispatch(setQualityIndex(plate, index));
    }

    nextQualityIndex(plate: number) {
        this.store.dispatch(nextQualityIndex(plate));
    }

    previousQualityIndex(plate: number) {
        this.store.dispatch(previousQualityIndex(plate));
    }

    retrievePlateCurves(plate: ?number = null) {
        if (plate != null) {
            this.setPlate(plate);
        }
        this.store.dispatch(retrievePlateCurves());
    }
}

export default function Bridge(store: Store) {
    const actions = new Actions(store);
    const selectors = new Selectors(store);
    const subscribe: (() => void) => void = callback => store.subscribe(callback);
    return {
        actions,
        selectors,
        subscribe,
    };
}