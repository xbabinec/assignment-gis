var mapLayerGroup = L.layerGroup();
var sportList = [];
const url = '/api/v1.0/';


function loadGymPoints(streetName, streetNumber, dist) {
  var request = new XMLHttpRequest();
  var params = "?dist=" + dist + "&streetName=" + streetName + "&streetNumber=" + streetNumber;
  request.open('GET', url + 'gym' + params, true);
  
  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var gymData = JSON.parse(request.responseText);
      gymData['type'] = 'FeatureCollection';
      var gymLayer = L.mapbox.featureLayer(gymData);
      mapLayerGroup.clearLayers();
      mapLayerGroup.addLayer(gymLayer);
    } else {
      alert("Load Error");
    }
  };
  request.onerror = function () {
    alert("Connection Error");
  };
  request.send();
}


function renderGymPoints() {
  var streetNumber = document.getElementById("streetNumber").value;
  var streetName = document.getElementById("streetName").value;
  var dist = document.getElementById("distance").value;
  loadGymPoints(streetName, streetNumber, dist);
  mapLayerGroup.addTo(map);
}


function loadPitchSportList() {
  var request = new XMLHttpRequest();
  request.open('GET', url + 'pitchSport', true);
  
  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var pitchSportData = JSON.parse(request.responseText);
      sportList = pitchSportData.slice();
      document.getElementById('dropdownSportList').appendChild(makeUl(sportList.slice()));
    } else {
      alert("Load Error");
    }
  };
  request.onerror = function () {
    alert("Connection Error");
  };
  request.send();
}


function loadPitchPolygons(sportType){
  var request = new XMLHttpRequest();
  var params = "?sportType=" + sportType;
  request.open('GET', url + 'pitch' + params, true);
  
  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var pitchData = JSON.parse(request.responseText);
      pitchData['type'] = 'FeatureCollection';
      var pitchLayer = L.mapbox.featureLayer(pitchData);
      mapLayerGroup.clearLayers();
      mapLayerGroup.addLayer(pitchLayer);
    } else {
      alert("Load Error");
    }
  };
  request.onerror = function () {
    alert("Connection Error");
  };
  request.send();
}


function renderPitchPolygons(){
  var dropDownBtn = document.getElementById("dropdownButton");
  var dropDownBtnTxt = dropDownBtn.childNodes[0];
  loadPitchPolygons(dropDownBtnTxt.nodeValue);
  mapLayerGroup.addTo(map);
}


function loadCityAreaRunningShapes(areaName){
  var request = new XMLHttpRequest();
  var params = "?areaName=" + areaName;
  request.open('GET', url + 'cityAreaRunning' + params, true);
  
  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var cityAreaData = JSON.parse(request.responseText);
      cityAreaData['type'] = 'FeatureCollection';
      var cityAreaLayer = L.mapbox.featureLayer(cityAreaData);
      mapLayerGroup.clearLayers();
      mapLayerGroup.addLayer(cityAreaLayer);
    } else {
      alert("Load Error");
    }
  };
  request.onerror = function () {
    alert("Connection Error");
  };
  request.send();
}


function renderCityAreaRunningShapes() {
  var areaName = document.getElementById('cityArea').value;
  loadCityAreaRunningShapes(areaName);
  mapLayerGroup.addTo(map);
}


function initSliderRange() {
  var slider = document.getElementById("distance");
  var output = document.getElementById("demo");
  output.innerHTML = slider.value;
  slider.oninput = function () {
    output.innerHTML = this.value;
  };
}


function makeUl(array) {
  var list = document.createElement('ul');
  list.className = "dropdown-menu";
  for (var i = 0; i < array.length; i++) {
    var item = document.createElement('li');
    item.appendChild(document.createTextNode(array[i]));
    item.setAttribute('id', 'list' + i);
    item.setAttribute('class', 'sport-li');
    item.onclick = function () {
      var dropdownButton = document.getElementById("dropdownButton");
      var dropdownBtnText = dropdownButton.childNodes[0];
      dropdownBtnText.nodeValue = this.innerHTML;
    };
    list.appendChild(item);
  }
  return list;
}