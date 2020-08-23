// Copyright 2012 Gray Designs. All Rights Reserved.
/*
 * @author rocky.grayjr@gmail.com (Rocky Gray)
 * @date July 31, 2012
 */

console.log("file loaded");

window.onload = function() {
  var tl = new TimelineMax();
  MorphSVGPlugin.convertToPath('circle');
  tl.to('#circle1', 1, {morphSVG: { shape: '#logo-top' }})
  tl.to('#circle2', 1, {morphSVG: { shape: '#logo-middle', type: 'rotational' }}, 0)
  tl.to('#circle3', 1, {morphSVG: { shape: '#logo-bottom' }}, 0)
};
