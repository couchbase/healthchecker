/**
 *
 * Copyright 2012, Couchbase, Inc.
 * All Rights Reserved
 *
 * Licensed under the Apache License, Version 2.0 (the "License")
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 **/

Zepto(function($) {
  /** utility functions **/
  function pxToNumber(css_px_value) {
    return Number(css_px_value.replace('px', ''));
  }

  /** DOM stuff **/
  $.getJSON('all.json',
  function(data) {
    dates = _.groupBy(data,
        function(name) {
          return name.split('_')[0]
        });

    thead = '<thead><tr>';
    $.each(dates, function(key, val) {
      thead += '<th colspan="' + val.length + '">' + key + '</th>';
    });
    thead += '</tr></thead>';

    tbody = '<tbody><tr>';
    $.each(dates, function(key, val) {
      $.each(val, function(i, time) {
        tbody += '<td><a href="' +  time + '.html">'
              + time.split('_')[1].substr(0, 5).replace('-', ':')
              + '</a></td>';
      });
    });
    tbody += '</tr></tbody>';

    $table = $('<table>' + thead + tbody + '</table>')
      .appendTo('#reports');

    var intervalID,
        right_start = pxToNumber($table.css('right')),
        left_start = ($(window).width()
                      - ($(window).width()-$('#next').offset().left)
                      - $table.width());
    function startMoving(direction) {
      intervalID = setInterval(function() { move(direction); }, 50);
    }

    function move(direction) {
      var right = pxToNumber($table.css('right')),
          left = pxToNumber($table.css('left'));
      if (direction === 'right' && right >= right_start) {
        stopMoving();
      } else if (direction === 'left' && right <= left_start) {
        stopMoving();
      } else {
        $table.animate({right: right + (direction === 'left' ? -10 : 10)});
      }
    }

    function stopMoving() {
      clearInterval(intervalID);
    }

    $('#prev').on('mouseenter', function() {
      startMoving('left');
    }).on('mouseleave', function() {
      stopMoving();
    });

    $('#next').on('mouseenter', function() {
      startMoving('right');
    }).on('mouseleave', function() {
      stopMoving();
    });
  });
});
