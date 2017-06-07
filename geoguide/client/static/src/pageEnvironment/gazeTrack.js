'use strict'

window.GeoGuide = window.GeoGuide || {}
import throttle from 'lodash/throttle'

export const initTracking = (handlerTrack)  => {
  if (!xLabs.extensionVersion()) { alert('xLabs extension not installed') }

  var Demo = {
    update : throttle(() => {
      //  var x = xLabs.getConfig( "state.head.x" );
      //  var y = xLabs.getConfig( "state.head.y" );
      //  var targetElement = document.getElementById( "target" );
      //  targetElement.style.left = ( screen.width * 0.5 ) - ( x * 300 ) + 'px';
      //  targetElement.style.top = ( screen.height * 0.5 ) + ( y * 300 ) + 'px';
      var trackingSuspended = parseInt( xLabs.getConfig( "state.trackingSuspended" ) );
      var calibrationStatus = parseInt( xLabs.getConfig( "calibration.status" ) );

      if( ( calibrationStatus == 0 ) || ( trackingSuspended == 1 ) ) {
        console.log('suspenso');
        return;
      }
      var xs = parseFloat( xLabs.getConfig( "state.gaze.estimate.x" ) );
      var ys = parseFloat( xLabs.getConfig( "state.gaze.estimate.y" ) );
      var x = xLabs.scr2docX( xs );
      var y = xLabs.scr2docY( ys );
      var c = parseFloat( xLabs.getConfig( "state.calibration.confidence" ) );
      console.log('confiança: ', c);
      handlerTrack(x, y);
    }, 200),
     ready : function() {
       xLabs.setConfig( "system.mode", "learning" );
       xLabs.setConfig( "browser.canvas.paintLearning", "0" );
     }
   }

   window.addEventListener( "beforeunload", function() {
     xLabs.setConfig( "system.mode", "off" );
   });

  xLabs.setup( Demo.ready, Demo.update, null, "24122d23-2651-471c-a168-8446b63b271c" );
};
