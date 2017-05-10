'use strict'

window.GeoGuide = window.GeoGuide || {}
import throttle from 'lodash/throttle'

export const initTracking = (handlerTrack)  => {
  if (!xLabs.extensionVersion()) { alert('extension not installed') }

  var Demo = {
    update : throttle(() => {
       var x = xLabs.getConfig( "state.head.x" );
       var y = xLabs.getConfig( "state.head.y" );
       var targetElement = document.getElementById( "target" );
       targetElement.style.left = ( screen.width * 0.5 ) - ( x * 300 ) + 'px';
       targetElement.style.top = ( screen.height * 0.5 ) + ( y * 300 ) + 'px';
       handlerTrack(x, y);
     }, 200),
     ready : function() {
       xLabs.setConfig( "system.mode", "head" );
       xLabs.setConfig( "browser.canvas.paintHeadPose", "0" );
     }
   }

  xLabs.setup( Demo.ready, Demo.update, null, "24122d23-2651-471c-a168-8446b63b271c" );
  console.log('setupou');
};
