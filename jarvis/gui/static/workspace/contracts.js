/**
 * Aria Living Workspace — Room / Tool / Activity contracts (Phase 2).
 * Rooms are NOT redesigned here — only interfaces future rooms will implement.
 */
(function () {
  "use strict";

  /**
   * @typedef {'minimal'|'standard'|'systems'|'focus'} ChromePolicy
   */

  /**
   * @typedef {object} RoomContract
   * @property {string} id
   * @property {'room'} kind
   * @property {string} metaphor
   * @property {string} hero
   * @property {string} viewId          existing panel adapter (temporary)
   * @property {ChromePolicy} chromePolicy
   * @property {string[]} [tools]       contextual tool ids
   * @property {string} [voice]
   */

  /**
   * @typedef {object} ToolContract
   * @property {string} id
   * @property {'tool'} kind
   * @property {string} label
   * @property {string} [viewId]        optional existing panel
   * @property {'sheet'|'spotlight'|'hud'|'mission'} surface
   * @property {string} [invoke]        action hint
   */

  /**
   * @typedef {object} ActivityContract
   * @property {string} id
   * @property {'activity'} kind
   * @property {string} title
   * @property {string[]} intentHints
   * @property {string} primaryRoom
   * @property {string[]} [supportingRooms]
   * @property {string[]} tools
   * @property {ChromePolicy} chromePolicy
   * @property {string} exitBehavior
   * @property {string} recipe          inspectable composition (always)
   */

  window.AriaWorkspaceContracts = {
    /** Validate a room descriptor without implementing immersive UI. */
    assertRoom(room) {
      const need = ["id", "kind", "metaphor", "hero", "viewId", "chromePolicy"];
      for (const k of need) {
        if (!room || room[k] == null || room[k] === "") {
          throw new Error(`RoomContract missing ${k}`);
        }
      }
      if (room.kind !== "room") throw new Error("kind must be room");
      return true;
    },
    assertTool(tool) {
      const need = ["id", "kind", "label", "surface"];
      for (const k of need) {
        if (!tool || tool[k] == null || tool[k] === "") {
          throw new Error(`ToolContract missing ${k}`);
        }
      }
      return true;
    },
    assertActivity(act) {
      const need = ["id", "kind", "title", "primaryRoom", "chromePolicy", "recipe"];
      for (const k of need) {
        if (!act || act[k] == null || act[k] === "") {
          throw new Error(`ActivityContract missing ${k}`);
        }
      }
      if (!Array.isArray(act.intentHints)) throw new Error("intentHints required");
      return true;
    },
  };
})();
