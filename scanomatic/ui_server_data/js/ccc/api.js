const GetSliceImagePath = "/api/calibration/#0#/image/#1#/slice/get/#2#";
const InitiateCCCPath = "/api/calibration/initiate_new";
const GetFixtruesPath = "/api/data/fixture/names";
const GetPinningFormatsPath = "/api/analysis/pinning/formats";
const GetTranposedMarkerPath = "/api/data/fixture/calculate/";
const GetGrayScaleAnalysisPath = "/api/data/grayscale/image/";


class API {
    static get(url) {
        return new Promise((resolve, reject) => $.ajax({
            url,
            type: 'GET',
            success: resolve,
            error: jqXHR => reject(JSON.parse(jqXHR.responseText).reason),
        }));
    }

    static postFormData(url, formData) {
        return new Promise((resolve, reject) => $.ajax({
            url,
            type: 'POST',
            contentType: false,
            enctype: 'multipart/form-data',
            data: formData,
            processData: false,
            success: resolve,
            error: jqXHR => reject(JSON.parse(jqXHR.responseText).reason),
        }));
    }

    static postJSON(url, json) {

        return new Promise(
            (resolve, reject) => $.ajax({
                url,
                type: 'POST',
                data: JSON.stringify(json),
                contentType: 'application/json',
            })
            .then(
                resolve,
                jqXHR => reject(JSON.parse(jqXHR.responseText).reason)));
    }
}

export function GetSliceImageURL(cccId, imageId, slice) {
    var path = GetSliceImagePath.replace("#0#", cccId).replace("#1#", imageId).replace("#2#", slice);
    return path;
}

export function GetSliceImage(cccId, imageId, slice, successCallback, errorCallback) {
    var path = GetSliceImagePath.replace("#0#", cccId).replace("#1#", imageId).replace("#2#", slice);

    $.get(path, successCallback).fail(errorCallback);
}


export function GetFixtures() {
    return API.get('/api/data/fixture/names').then(data => data.fixtures);
}

function GetFixtureData(fixtureName) {
    var path = `/api/data/fixture/get/${fixtureName}`;
    return API.get(path);
}

export function GetFixturePlates(fixtureName) {
    return GetFixtureData(fixtureName).then(data => data.plates);
}

export function GetPinningFormats() {
    return API.get('/api/analysis/pinning/formats')
        .then(data => data.pinning_formats.map(({ name, value }) => {
            return { name, nCols: value[0], nRows: value[1] };
        }));
}

export function GetPinningFormatsv2(successCallback, errorCallback) {
    var path = GetPinningFormatsPath;

    $.ajax({
        url: path,
        type: "GET",
        success: successCallback,
        error: errorCallback
    });
};

export function InitiateCCC(species, reference, successCallback, errorCallback) {
    const formData = new FormData();
    formData.append('species', species);
    formData.append('reference', reference);
    return API.postFormData('/api/calibration/initiate_new', formData);
}

export function SetCccImageData(cccId, imageId, accessToken, dataArray, fixture) {
    var path = `/api/calibration/${cccId}/image/${imageId}/data/set`;
    var formData = new FormData();
    formData.append("ccc_identifier", cccId);
    formData.append("image_identifier", imageId);
    formData.append("access_token", accessToken);
    formData.append("fixture", fixture);
    for (var i = 0; i < dataArray.length; i++) {
        var item = dataArray[i];
        formData.append(item.key, item.value);
    }
    return API.postFormData(path, formData);
}

export function SetCccImageSlice(cccId, imageId, accessToken) {
    var path = `/api/calibration/${cccId}/image/${imageId}/slice/set`;
    var formData = new FormData();
    formData.append("access_token", accessToken);
    return API.postFormData(path, formData);
}

export function SetGrayScaleImageAnalysis(cccId, imageId, accessToken) {
    var path = `/api/calibration/${cccId}/image/${imageId}/grayscale/analyse`;
    var formData = new FormData();
    formData.append("access_token", accessToken);
    return API.postFormData(path, formData);
}

export function GetGrayScaleAnalysis(grayScaleName, imageData, successCallback, errorCallback) {
    var path = GetGrayScaleAnalysisPath + grayScaleName;
    var formData = new FormData();
    formData.append("image", imageData);
    $.ajax({
        url: path,
        type: "POST",
        contentType: false,
        enctype: 'multipart/form-data',
        data: formData,
        processData: false,
    });
}

export function SetGrayScaleTransform(cccId, imageId, plate, accessToken) {
    var path = `/api/calibration/${cccId}/image/${imageId}/plate/${plate}/transform`;
    var formData = new FormData();
    formData.append("access_token", accessToken);
    return API.postFormData(path, formData);
}

export function SetGridding(cccId, imageId, plate, pinningFormat, offSet, accessToken) {
    var path = `/api/calibration/${cccId}/image/${imageId}/plate/${plate}/grid/set`;
    return new Promise((resolve, reject) => $.ajax({
        url: path,
        type: "POST",
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({
            pinning_format: pinningFormat,
            gridding_correction: offSet,
            access_token: accessToken,
        }),
        success: resolve,
        error: jqXHR => reject(JSON.parse(jqXHR.responseText)),
    }));
}

export function SetColonyDetection(cccId, imageId, plate, accessToken, row, col, successCallback, errorCallback) {
    var path = `/api/calibration/${cccId}/image/${imageId}/plate/${plate}/detect/colony/${col}/${row}`;

    var formData = new FormData();
    formData.append("access_token", accessToken);
    $.ajax({
        url: path,
        type: "POST",
        contentType: false,
        enctype: 'multipart/form-data',
        data: formData,
        processData: false,
        success: data => successCallback(data),
        error: (jqXHR) => errorCallback(JSON.parse(jqXHR.responseText)),
    });
}

export function SetColonyCompression(cccId, imageId, plate, accessToken, colony, cellCount, row, col, successCallback, errorCallback) {
    var path = `/api/calibration/${cccId}/image/${imageId}/plate/${plate}/compress/colony/${col}/${row}`;

    var data = {
        access_token: accessToken,
        image: colony.image,
        blob: colony.blob,
        background: colony.background,
        cell_count: cellCount,
    };
    $.ajax({
        url: path,
        method: "POST",
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function (data) {
            successCallback(data);
        },
        error: (jqXHR) => errorCallback(JSON.parse(jqXHR.responseText)),
    });
}

export function GetImageId(cccId, file, accessToken) {
    var path = `/api/calibration/${cccId}/add_image`;
    var formData = new FormData();
    formData.append("image", file);
    formData.append("access_token", accessToken);
    return API.postFormData(path, formData);
}

export function GetMarkers(fixtureName, file) {
    var path = `/api/data/markers/detect/${fixtureName}`;
    var formData = new FormData();
    formData.append("image", file);
    formData.append("save", "false");
    return API.postFormData(path, formData);
}

export function GetTransposedMarkersV2(fixtureName, markers, file, successCallback, errorCallback) {
    var path = GetTranposedMarkerPath + fixtureName;
    var formData = new FormData();
    formData.append("image", file);
    formData.append("markers", markers);
    $.ajax({
        url: path,
        type: "POST",
        contentType: false,
        enctype: 'multipart/form-data',
        data: formData,
        processData: false,
        success: successCallback,
        error: errorCallback
    });
}

export function GetTransposedMarkers(fixtureName, markers, successCallback, errorCallback) {
    var path = GetTranposedMarkerPath + fixtureName;
    var formData = new FormData();
    formData.append("markers", markers);
    $.ajax({
        url: path,
        type: "POST",
        contentType: false,
        enctype: 'multipart/form-data',
        data: formData,
        processData: false,
        success: successCallback,
        error: errorCallback
    });
}

export function SetNewCalibrationPolynomial(cccId, power, accessToken) {
    return API.postJSON(
        `/api/calibration/${cccId}/construct/${power}`,
        {access_token: accessToken},
    );
}
