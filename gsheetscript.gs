/**
 * The event handler triggered when opening the spreadsheet.
 * @param {Event} e The onOpen event.
 */
function onOpen(e) {
  getAndWriteCells()
}

function onEdit(e) {
  // In testing this function seems to trigger when a column is added, but not when a column is deleted. 
  // Also not when a tab has it's name changed. Seems that not all edits will fire this.  
  
  // Catch column change in column D
  //if (e.range.getNumColumns() === 1 && e.range.getColumn() === 4) {
  //    getAndWriteCells();
  //}
  
  // Catch cell change in cell D1
  if (e.range.getA1Notation() === "D1") {
    console.log("Cell D1 was changed to: " + e.range.getValue());
    if (e.range.getValue().substring(0, 2) === "ww" && /^\d\d$/.test(e.range.getValue().substring(2, 4))) {
      getAndWriteCells();
    }
  }
}


/*** 
*
* 2020-10-10 | Ciaran Murphy
*
* Method to auto-populate the cells in a Google Spreadsheet based on certain trigger events.
*
***/
function getAndWriteCells() {
  SpreadsheetApp.getActiveSpreadsheet().toast('', 'Update to current work task started...', 5);
  
  var CURRENT_WEEK_CELL = 'D1';                                 // Should be a 'ww'' followed by a number, e.g. 'ww42'
  var TOPIC_COL_IN_TRACKER_A1 = 'A:A';                          // The column in the tracker that shows the topic of work
  var TOPIC_COL_IN_TRACKER_INT = 0;
  var TOPIC_HEADER_STRING = 'Topic';                            // The string in the heading of the column for the topic. This has to be filtered out from the column scan
  var PLANNER_WORKPACKAGE_COL = 2;                              // The column in the planner where the work packages are listed
  var CUR_WOK_COL_INT = 2;                                      // The column where the current and next work should be entered

  var sheet = SpreadsheetApp.getActive();
  var tracker = sheet.getSheetByName('Tab2');
  var planner = sheet.getSheetByName('Tab1');
  
  var current_week_number = Number(tracker.getRange(CURRENT_WEEK_CELL).getValue().substring(2, 4));
  var current_week_string = 'ww' + current_week_number;
  var next_week_number = current_week_number + 1;
  var next_week_string = 'ww' + next_week_number;
  console.log("Current week: " + current_week_string + ", next week: " + next_week_string);

  var planning_data = planner.getDataRange();
  var planning_data_values = planner.getDataRange().getValues();

  var total_rows = planning_data.getHeight();
  var total_cols = planning_data.getWidth();
  var cur_week_col = -1;
  var next_week_col = -1;

  // Tried using the findString() stuff in Google Script but it didn't work
  for (var i = 0; i<total_rows; i++) {
    for (var j = 0; j<total_cols; j++) {
      if (planning_data_values[i][j] == current_week_string) {
        cur_week_col = j;
        break;
      }
    }
    for (var j = 0; j<total_cols; j++) {
      if (planning_data_values[i][j] == next_week_string) {
        next_week_col = j;
        break;
      }
    }
  }
  
  var topic_col_data = tracker.getRange(TOPIC_COL_IN_TRACKER_A1).getValues();
  for (var idx in topic_col_data) {
    if (topic_col_data[idx] != '' && topic_col_data[idx] != TOPIC_HEADER_STRING) {
      topic = topic_col_data[idx];
      console.log("Working on topic: " + topic[0]);

      var current_planned_work_string = "This weeks planned work:";
      var next_planned_work_string = "Next weeks planned work:";
      for (var i=0; i<total_rows; i++) {
        if (planning_data_values[i][TOPIC_COL_IN_TRACKER_INT] == topic) {
          if (Number(planning_data_values[i][cur_week_col]) > 0) {
            current_planned_work_string += '\n-> ' + planning_data_values[i][PLANNER_WORKPACKAGE_COL];
          }
          if (next_week_col != -1 && Number(planning_data_values[i][next_week_col]) > 0) {
            next_planned_work_string += '\n-> ' + planning_data_values[i][PLANNER_WORKPACKAGE_COL];
          }
        }
      }
      // I have to add 1 to the indices below because the method getRange() uses a 1 based index, not zero!
      tracker.getRange(Number(idx)+1, CUR_WOK_COL_INT+1).setValue(current_planned_work_string);
      tracker.getRange(Number(idx)+2, CUR_WOK_COL_INT+1).setValue(next_planned_work_string);
    }
  }
  tracker.autoResizeRows(1, tracker.getDataRange().getHeight());
  
  SpreadsheetApp.getActiveSpreadsheet().toast('', 'Update to current work task finished.', 5);
}
