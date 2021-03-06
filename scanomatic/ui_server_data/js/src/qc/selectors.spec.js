import * as selectors from './selectors';
import StateBuilder from './StateBuilder';

describe('/qc/selectors', () => {
    it('should get the project path', () => {
        const state = new StateBuilder().setProject('/my/path').build();
        expect(selectors.getProject(state)).toEqual('/my/path');
    });

    it('should get phenotype', () => {
        const state = new StateBuilder()
            .setProject('/my/path')
            .setPhenotype('test')
            .build();
        expect(selectors.getPhenotype(state)).toEqual('test');
    });

    it('should get phenotype data', () => {
        const state = new StateBuilder()
            .setProject('/my/path')
            .setPhenotype('test2')
            .setPlatePhenotypeData(
                'test',
                [[5, 4, 3], [5, 5, 1]],
            )
            .build();
        expect(selectors.getPhenotypeData(state, 'test'))
            .toEqual([
                [5, 4, 3],
                [5, 5, 1],
            ]);
    });

    it('should get current phenotype data', () => {
        const state = new StateBuilder()
            .setProject('/my/path')
            .setPhenotype('test')
            .setPlatePhenotypeData(
                'test',
                [[5, 4, 3], [5, 5, 1]],
                new Map([
                    ['BadData', [[0], [0]]],
                    ['Empty', [[0], [1]]],
                    ['NoGrowth', [[1, 1], [0, 1]]],
                    ['UndecidedProblem', [[1, 0], [2, 2]]],
                ]),
            )
            .build();
        expect(selectors.getCurrentPhenotypeData(state))
            .toEqual([
                [5, 4, 3],
                [5, 5, 1],
            ]);
    });

    it('should get the QC Marks for current phenotype', () => {
        const state = new StateBuilder()
            .setProject('/my/path')
            .setPhenotype('test')
            .setPlatePhenotypeData(
                'test',
                [[5, 4, 3], [5, 5, 1]],
                new Map([
                    ['BadData', [[0], [0]]],
                    ['Empty', [[0], [1]]],
                    ['NoGrowth', [[1, 1], [0, 1]]],
                    ['UndecidedProblem', [[1, 0], [2, 2]]],
                ]),
            )
            .build();
        expect(selectors.getCurrentPhenotypeQCMarks(state))
            .toEqual(new Map([
                ['BadData', [[0], [0]]],
                ['Empty', [[0], [1]]],
                ['NoGrowth', [[1, 1], [0, 1]]],
                ['UndecidedProblem', [[1, 0], [2, 2]]],
            ]));
    });

    it('should get the plate number', () => {
        const state = new StateBuilder().setPlate(2).build();
        expect(selectors.getPlate(state)).toEqual(2);
    });

    describe('raw data', () => {
        it('should return null if curve is on wrong plate', () => {
            const state = new StateBuilder().build();
            expect(selectors.getRawCurve(state, 2, 4, 4)).toBe(null);
        });

        it('should return null if curve not yet loaded', () => {
            const state = new StateBuilder().build();
            expect(selectors.getRawCurve(state, 0, 4, 4)).toBe(null);
        });

        it('should return the growth data', () => {
            const state = new StateBuilder()
                .setPlate(1)
                .setPlateGrowthData(
                    1,
                    [1, 2, 3],
                    [[[2, 3, 4], [4, 2, 1]]],
                    [[[6, 6, 6], [1, 4, 5]]],
                )
                .build();
            expect(selectors.getRawCurve(state, 1, 0, 1)).toEqual([4, 2, 1]);
        });
    });

    describe('smooth data', () => {
        it('should return null if curve is on wrong plate', () => {
            const state = new StateBuilder().build();
            expect(selectors.getSmoothCurve(state, 2, 4, 4)).toBe(null);
        });

        it('should return null if curve not yet loaded', () => {
            const state = new StateBuilder().build();
            expect(selectors.getSmoothCurve(state, 0, 4, 4)).toBe(null);
        });

        it('should return the growth data', () => {
            const state = new StateBuilder()
                .setPlate(1)
                .setPlateGrowthData(
                    1,
                    [1, 2, 3],
                    [[[2, 3, 4], [4, 2, 1]]],
                    [[[6, 6, 6], [1, 4, 5]]],
                )
                .build();
            expect(selectors.getSmoothCurve(state, 1, 0, 1)).toEqual([1, 4, 5]);
        });
    });

    describe('times', () => {
        it('should get the times of the growth curve if plate is right', () => {
            const state = new StateBuilder()
                .setPlateGrowthData(
                    0,
                    [1, 2, 3],
                    [[[2, 3, 4]]],
                    [[[6, 6, 6]]],
                )
                .build();
            expect(selectors.getTimes(state, 0)).toEqual([1, 2, 3]);
        });

        it('should return null if plate is wrong', () => {
            const state = new StateBuilder()
                .setPlateGrowthData(
                    0,
                    [1, 2, 3],
                    [[[2, 3, 4]]],
                    [[[6, 6, 6]]],
                )
                .build();
            expect(selectors.getTimes(state, 1)).toEqual(null);
        });
    });

    describe('getFocus', () => {
        const queue = [
            { idx: 0, col: 1, row: 1 },
            { idx: 1, col: 0, row: 1 },
            { idx: 2, col: 1, row: 0 },
            { idx: 3, col: 0, row: 0 },
        ];

        it('should return null if no queue', () => {
            const state = new StateBuilder().build();
            expect(selectors.getFocus(state)).toBe(null);
        });

        it('should return current index info', () => {
            const state = new StateBuilder()
                .setQualityIndexQueue(queue)
                .setQualityIndex(1)
                .build();
            expect(selectors.getFocus(state)).toEqual({
                idx: 1,
                col: 0,
                row: 1,
            });
        });
    });

    describe('getQIndexFromPosition', () => {
        const queue = [
            { idx: 0, col: 1, row: 1 },
            { idx: 1, col: 0, row: 1 },
            { idx: 2, col: 1, row: 0 },
            { idx: 3, col: 0, row: 0 },
        ];

        it('should return null if no queue', () => {
            const state = new StateBuilder().build();
            expect(selectors.getQIndexFromPosition(state, 1, 0)).toBe(null);
        });

        it('should return index for position', () => {
            const state = new StateBuilder()
                .setQualityIndexQueue(queue)
                .setQualityIndex(1)
                .build();
            expect(selectors.getQIndexFromPosition(state, 1, 0)).toEqual(1);
        });

        it('should return undefined for unknown position', () => {
            const state = new StateBuilder()
                .setQualityIndexQueue(queue)
                .setQualityIndex(1)
                .build();
            expect(selectors.getQIndexFromPosition(state, 10, 0)).toBe(undefined);
        });
    });

    describe('getFocusCurveQCMark', () => {
        const queue = [
            { idx: 0, row: 1, col: 1 },
            { idx: 1, row: 1, col: 0 },
            { idx: 2, row: 0, col: 1 },
            { idx: 3, row: 0, col: 0 },
        ];

        it('should return null if no qcmarks gotten', () => {
            const state = new StateBuilder().build();
            expect(selectors.getFocusCurveQCMark(state)).toBe(null);
        });

        it('should return null if no focus curve', () => {
            const state = new StateBuilder()
                .setProject('my/project')
                .setPhenotype('GenerationTime')
                .build();
            expect(selectors.getFocusCurveQCMark(state)).toBe(null);
        });

        it('returns OK if no mark', () => {
            const state = new StateBuilder()
                .setProject('my/project')
                .setPlate(0)
                .setPhenotype('GenerationTime')
                .setQualityIndexQueue(queue)
                .setPlatePhenotypeData(
                    'GenerationTime',
                    [[]],
                    new Map(),
                )
                .build();
            expect(selectors.getFocusCurveQCMark(state)).toBe('OK');
        });

        describe('marks', () => {
            const builder = new StateBuilder()
                .setProject('my/project')
                .setPlate(0)
                .setPhenotype('GenerationTime')
                .setQualityIndexQueue(queue)
                .setPlatePhenotypeData(
                    'GenerationTime',
                    [[]],
                    new Map([
                        ['BadData', [[0], [0]]],
                        ['Empty', [[0], [1]]],
                        ['NoGrowth', [[1], [0]]],
                        ['UndecidedProblem', [[1], [1]]],
                    ]),
                );

            it('returns BadData if BadData', () => {
                const state = builder
                    .setQualityIndex(3)
                    .build();
                expect(selectors.getFocusCurveQCMark(state)).toBe('BadData');
            });

            it('returns NoGrowth if NoGrowth', () => {
                const state = builder
                    .setQualityIndex(1)
                    .build();
                expect(selectors.getFocusCurveQCMark(state)).toBe('NoGrowth');
            });

            it('returns Empty if Empty', () => {
                const state = builder
                    .setQualityIndex(2)
                    .build();
                expect(selectors.getFocusCurveQCMark(state)).toBe('Empty');
            });

            it('returns UndecidedProblem if UndecidedProblem', () => {
                const state = builder
                    .setQualityIndex(0)
                    .build();
                expect(selectors.getFocusCurveQCMark(state)).toBe('UndecidedProblem');
            });
        });
    });

    describe('getFocusCurveQCMarkAllPhenotypes', () => {
        it('returns null if no qcmarks', () => {
            const state = new StateBuilder()
                .setProject('my/project')
                .setPlate(0)
                .setPhenotype('GenerationTime')
                .build();
            expect(selectors.getFocusCurveQCMark(state)).toBe(null);
        });

        it('returns an object that maps phenotypes to marks', () => {
            const queue = [
                { idx: 0, row: 0, col: 0 },
            ];
            const state = new StateBuilder()
                .setProject('my/project')
                .setPlate(0)
                .setPhenotype('GenerationTime')
                .setQualityIndexQueue(queue)
                .setPlatePhenotypeData(
                    'GenerationTime',
                    [[]],
                    new Map([['BadData', [[0], [0]]]]),
                )
                .setPlatePhenotypeData(
                    'GenerationTimeWhen',
                    [[]],
                    new Map([['NoGrowth', [[0], [0]]]]),
                )
                .setPlatePhenotypeData(
                    'ExperimentGrowthYield',
                    [[]],
                    new Map([['Empty', [[1], [1]]]]),
                )
                .setQualityIndex(0)
                .build();
            expect(selectors.getFocusCurveQCMarkAllPhenotypes(state))
                .toEqual(new Map([
                    ['GenerationTime', 'BadData'],
                    ['GenerationTimeWhen', 'NoGrowth'],
                    ['ExperimentGrowthYield', 'OK'],
                ]));
        });
    });

    describe('isDirty', () => {
        it('returns false if nothing set', () => {
            const state = new StateBuilder()
                .build();
            expect(selectors.isDirty(state, 0, 0, 0)).toBe(false);
        });

        it('returns false if nothing has yet been dirty', () => {
            const state = new StateBuilder()
                .setProject('my/experiment')
                .setPhenotype('GenerationTime')
                .build();
            expect(selectors.isDirty(state, 0, 0, 0)).toBe(false);
        });

        it('returns true if position is dirty', () => {
            const state = new StateBuilder()
                .setProject('my/experiment')
                .setPhenotype('GenerationTime')
                .setDirty(0, 0)
                .setDirty(1, 2)
                .build();
            expect(selectors.isDirty(state, 0, 0, 0)).toBe(true);
            expect(selectors.isDirty(state, 0, 1, 2)).toBe(true);
        });

        it('returns failse if position is not dirty', () => {
            const state = new StateBuilder()
                .setProject('my/experiment')
                .setPhenotype('GenerationTime')
                .setDirty(0, 0)
                .setDirty(1, 2)
                .build();
            expect(selectors.isDirty(state, 0, 0, 10)).toBe(false);
        });
    });
});
