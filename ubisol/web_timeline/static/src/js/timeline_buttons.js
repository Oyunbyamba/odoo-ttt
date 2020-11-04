odoo.define('web.TimelineButtons', function (require) {
    "use strict";
    
    var core = require('web.core');
    var config = require('web.config');
    var BasicController = require('web.BasicController');
    var DataExport = require('web.DataExport');
    var Dialog = require('web.Dialog');
    var ListConfirmDialog = require('web.ListConfirmDialog');
    var Sidebar = require('web.Sidebar');
    
    var _t = core._t;
    var qweb = core.qweb;
    
    var TimelineButtons = BasicController.extend({
        buttons_template: 'TimelineView.buttons',
        events: _.extend({}, BasicController.prototype.events, {
            'click .o_timeline_export_xlsx': '_onDirectExportData',
        }),
        custom_events: _.extend({}, BasicController.prototype.custom_events, {
            activate_next_widget: '_onActivateNextWidget',
            add_record: '_onAddRecord',
            button_clicked: '_onButtonClicked',
            group_edit_button_clicked: '_onEditGroupClicked',
            edit_line: '_onEditLine',
            save_line: '_onSaveLine',
            selection_changed: '_onSelectionChanged',
            toggle_column_order: '_onToggleColumnOrder',
            toggle_group: '_onToggleGroup',
        }),
        /**
         * @constructor
         * @override
         * @param {Object} params
         * @param {boolean} params.editable
         * @param {boolean} params.hasSidebar
         * @param {Object} params.toolbarActions
         * @param {boolean} params.noLeaf
         */
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.hasSidebar = params.hasSidebar;
            this.toolbarActions = params.toolbarActions || {};
            this.editable = params.editable;
            this.noLeaf = params.noLeaf;
            this.selectedRecords = params.selectedRecords || [];
            this.multipleRecordsSavingPromise = null;
            this.fieldChangedPrevented = false;
        },
    
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

        getActiveDomain: function () {
            var self = this;
            if (this.$('thead .o_timeline_record_selector input').prop('checked')) {
                var searchQuery = this._controlPanel ? this._controlPanel.getSearchQuery() : {};
                var record = self.model.get(self.handle, {raw: true});
                return record.getDomain().concat(searchQuery.domain || []);
            }
        },
        /*
         * @override
         */
        getOwnedQueryParams: function () {
            var state = this._super.apply(this, arguments);
            var orderedBy = this.model.get(this.handle, {raw: true}).orderedBy || [];
            return _.extend({}, state, {orderedBy: orderedBy});
        },
        getSelectedIds: function () {
            return _.map(this.getSelectedRecords(), function (record) {
                return record.res_id;
            });
        },
        getSelectedRecords: function () {
            var self = this;
            return _.map(this.selectedRecords, function (db_id) {
                return self.model.get(db_id, {raw: true});
            });
        },
        renderButtons: function ($node) {
            if (!this.noLeaf && this.hasButtons) {
                this.$buttons = $(qweb.render(this.buttons_template, {widget: this}));
                this.$buttons.on('click', '.o_timeline_button_add', this._onCreateRecord.bind(this));
    
                this._assignCreateKeyboardBehavior(this.$buttons.find('.o_timeline_button_add'));
                this.$buttons.find('.o_timeline_button_add').tooltip({
                    delay: {show: 200, hide: 0},
                    title: function () {
                        return qweb.render('CreateButton.tooltip');
                    },
                    trigger: 'manual',
                });
                this.$buttons.on('mousedown', '.o_timeline_button_discard', this._onDiscardMousedown.bind(this));
                this.$buttons.on('click', '.o_timeline_button_discard', this._onDiscard.bind(this));
                this.$buttons.find('.o_timeline_export_xlsx').toggle(!config.device.isMobile);
                this.$buttons.appendTo($node);
            }
        },
        renderSidebar: function ($node) {
            var self = this;
            if (this.hasSidebar) {
                var other = [{
                    label: _t("Export"),
                    callback: this._onExportData.bind(this)
                }];
                if (this.archiveEnabled) {
                    other.push({
                        label: _t("Archive"),
                        callback: function () {
                            Dialog.confirm(self, _t("Are you sure that you want to archive all the selected records?"), {
                                confirm_callback: self._toggleArchiveState.bind(self, true),
                            });
                        }
                    });
                    other.push({
                        label: _t("Unarchive"),
                        callback: this._toggleArchiveState.bind(this, false)
                    });
                }
                if (this.is_action_enabled('delete')) {
                    other.push({
                        label: _t('Delete'),
                        callback: this._onDeleteSelectedRecords.bind(this)
                    });
                }
                this.sidebar = new Sidebar(this, {
                    editable: this.is_action_enabled('edit'),
                    env: {
                        context: this.model.get(this.handle, {raw: true}).getContext(),
                        activeIds: this.getSelectedIds(),
                        model: this.modelName,
                    },
                    actions: _.extend(this.toolbarActions, {other: other}),
                });
                return this.sidebar.appendTo($node).then(function() {
                    self._toggleSidebar();
                });
            }
            return Promise.resolve();
        },
        update: function (params, options) {
            var self = this;
            if (options && options.keepSelection) {
                // filter out removed records from selection
                var res_ids = this.model.get(this.handle).res_ids;
                this.selectedRecords = _.filter(this.selectedRecords, function (id) {
                    return _.contains(res_ids, self.model.get(id).res_id);
                });
            } else {
                this.selectedRecords = [];
            }
    
            params.selectedRecords = this.selectedRecords;
            return this._super.apply(this, arguments);
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        _abandonRecord: function (recordID) {
            this._super.apply(this, arguments);
            if ((recordID || this.handle) !== this.handle) {
                var state = this.model.get(this.handle);
                this.renderer.removeLine(state, recordID);
                this._updatePager();
            }
        },
        _addRecord: function (dataPointId) {
            var self = this;
            this._disableButtons();
            return this.renderer.unselectRow().then(function () {
                return self.model.addDefaultRecord(dataPointId, {
                    position: self.editable,
                });
            }).then(function (recordID) {
                var state = self.model.get(self.handle);
                self.renderer.updateState(state, {keepWidths: true})
                    .then(function () {
                        self.renderer.editRecord(recordID);
                    }).then(self._updatePager.bind(self));
            }).then(this._enableButtons.bind(this)).guardedCatch(this._enableButtons.bind(this));
        },
        _archive: function (ids, archive) {
            if (ids.length === 0) {
                return Promise.resolve();
            }
            if (archive) {
                return this.model
                    .actionArchive(ids, this.handle)
                    .then(this.update.bind(this, {}, {reload: false}));
            } else {
                return this.model
                    .actionUnarchive(ids, this.handle)
                    .then(this.update.bind(this, {}, {reload: false}));
            }
        },
        _assignCreateKeyboardBehavior: function($createButton) {
            var self = this;
            $createButton.on('keydown', function(e) {
                $createButton.tooltip('hide');
                switch(e.which) {
                    case $.ui.keyCode.ENTER:
                        e.preventDefault();
                        self._onCreateRecord.apply(self);
                        break;
                    case $.ui.keyCode.DOWN:
                        e.preventDefault();
                        self.renderer.giveFocus();
                        break;
                    case $.ui.keyCode.TAB:
                        if (!e.shiftKey && e.target.classList.contains("btn-primary")) {
                            e.preventDefault();
                            $createButton.tooltip('show');
                        }
                        break;
                }
            });
        },
        _confirmSave: function (id) {
            var state = this.model.get(this.handle);
            return this.renderer.updateState(state, {noRender: true})
                .then(this._setMode.bind(this, 'readonly', id));
        },
        _discardChanges: function (recordID) {
            if ((recordID || this.handle) === this.handle) {
                recordID = this.renderer.getEditableRecordID();
                if (recordID === null) {
                    return Promise.resolve();
                }
            }
            var self = this;
            return this._super(recordID).then(function () {
                self._updateButtons('readonly');
            });
        },
        _getExportDialogWidget() {
            let state = this.model.get(this.handle);
            let defaultExportFields = this.renderer.columns.filter(field => field.tag === 'field').map(field => field.attrs.name);
            let groupedBy = this.renderer.state.groupedBy;
            return new DataExport(this, state, defaultExportFields, groupedBy,
                this.getActiveDomain(), this.getSelectedIds());
        },
        _getSidebarEnv: function () {
            var env = this._super.apply(this, arguments);
            var record = this.model.get(this.handle);
            return _.extend(env, {domain: record.getDomain()});
        },
        _isPagerVisible: function () {
            var state = this.model.get(this.handle, {raw: true});
            return !!state.count;
        },
        _saveMultipleRecords: function (recordId, node, changes) {
            var fieldName = Object.keys(changes)[0];
            var value = Object.values(changes)[0];
            var recordIds = _.union([recordId], this.selectedRecords);
            var validRecordIds = recordIds.reduce((result, nextRecordId) => {
                var record = this.model.get(nextRecordId);
                var modifiers = this.renderer._registerModifiers(node, record);
                if (!modifiers.readonly && (!modifiers.required || value)) {
                    result.push(nextRecordId);
                }
                return result;
            }, []);
            return new Promise((resolve, reject) => {
                const discardAndReject = () => {
                    this.model.discardChanges(recordId);
                    this._confirmSave(recordId).then(() => {
                        this.renderer.focusCell(recordId, node);
                        reject();
                    });
                };
                if (validRecordIds.length > 0) {
                    const dialogOptions = {
                        confirm_callback: () => {
                            this.model.saveRecords(this.handle, recordId, validRecordIds, fieldName)
                                .then(async () => {
                                    this._updateButtons('readonly');
                                    const state = this.model.get(this.handle);
                                    await this.renderer.updateState(state, { keepWidths: true });
                                    await this.renderer.focusCell(recordId, node);
                                    resolve(Object.keys(changes));
                                })
                                .guardedCatch(discardAndReject);
                        },
                        cancel_callback: discardAndReject,
                    };
                    const record = this.model.get(recordId);
                    const dialogChanges = {
                        fieldLabel: node.attrs.string || record.fields[fieldName].string,
                        fieldName: node.attrs.name,
                        nbRecords: recordIds.length,
                        nbValidRecords: validRecordIds.length,
                    };
                    new ListConfirmDialog(this, record, dialogChanges, dialogOptions)
                        .open({ shouldFocusButtons: true });
                } else {
                    Dialog.alert(this, _t("No valid record to save"), {
                        confirm_callback: discardAndReject,
                    });
                }
            });
        },
        _saveRecord: function (recordId) {
            var record = this.model.get(recordId, { raw: true });
            if (record.isDirty() && this.renderer.isInMultipleRecordEdition(recordId)) {
                // do not save the record (see _saveMultipleRecords)
                const prom = this.multipleRecordsSavingPromise || Promise.reject();
                this.multipleRecordsSavingPromise = null;
                return prom;
            }
            return this._super.apply(this, arguments);
        },
        _setMode: function (mode, recordID) {
            if ((recordID || this.handle) !== this.handle) {
                this.mode = mode;
                this._updateButtons(mode);
                return this.renderer.setRowMode(recordID, mode);
            } else {
                return this._super.apply(this, arguments);
            }
        },
        _toggleArchiveState: function (archive) {
            this._archive(this.selectedRecords, archive);
        },
        _toggleCreateButton: function () {
            if (this.$buttons) {
                var state = this.model.get(this.handle);
                var createHidden = this.renderer.isEditable() && state.groupedBy.length && state.data.length;
                this.$buttons.find('.o_timeline_button_add').toggleClass('o_hidden', !!createHidden);
            }
        },
        _toggleSidebar: function () {
            if (this.sidebar) {
                this.sidebar.do_toggle(this.selectedRecords.length > 0);
            }
        },
        _update: function () {
            return this._super.apply(this, arguments)
                .then(this._toggleSidebar.bind(this))
                .then(this._toggleCreateButton.bind(this))
                .then(this._updateButtons.bind(this, 'readonly'));
        },
        _updateButtons: function (mode) {
            if (this.$buttons) {
                this.$buttons.toggleClass('o-editing', mode === 'edit');
                const state = this.model.get(this.handle, {raw: true});
                if (state.count && !config.device.isMobile) {
                    this.$('.o_timeline_export_xlsx').show();
                } else {
                    this.$('.o_timeline_export_xlsx').hide();
                }
            }
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        _onActivateNextWidget: function (ev) {
            ev.stopPropagation();
            this.renderer.editFirstRecord(ev);
        },
        _onAddRecord: function (ev) {
            ev.stopPropagation();
            var dataPointId = ev.data.groupId || this.handle;
            if (this.activeActions.create) {
                this._addRecord(dataPointId);
            } else if (ev.data.onFail) {
                ev.data.onFail();
            }
        },
        _onButtonClicked: function (ev) {
            ev.stopPropagation();
            this._callButtonAction(ev.data.attrs, ev.data.record);
        },
        _onCreateRecord: function (ev) {
            if (ev) {
                ev.stopPropagation();
            }
            var state = this.model.get(this.handle, {raw: true});
            if (this.editable && !state.groupedBy.length) {
                this._addRecord(this.handle);
            } else {
                this.trigger_up('switch_view', {view_type: 'form', res_id: undefined});
            }
        },
        _onDeleteSelectedRecords: function () {
            this._deleteRecords(this.selectedRecords);
        },
        _onDiscard: function (ev) {
            ev.stopPropagation(); // So that it is not considered as a row leaving
            this._discardChanges();
        },
        _onDiscardMousedown: function (ev) {
            var self = this;
            this.fieldChangedPrevented = true;
            window.addEventListener('mouseup', function (mouseupEvent) {
                var preventedEvent = self.fieldChangedPrevented;
                self.fieldChangedPrevented = false;
                // If the user starts clicking (mousedown) on the button and stops clicking
                // (mouseup) outside of the button, we want to trigger the original onFieldChanged
                // Event that was prevented in the meantime.
                if (ev.target !== mouseupEvent.target && preventedEvent.constructor.name === 'OdooEvent') {
                    self._onFieldChanged(preventedEvent);
                }
            }, { capture: true, once: true });
        },
        _onEditLine: function (ev) {
            var self = this;
            ev.stopPropagation();
            this.trigger_up('mutexify', {
                action: function () {
                    self._setMode('edit', ev.data.recordId)
                        .then(ev.data.onSuccess);
                },
            });
        },
        _onExportData: function () {
            this._getExportDialogWidget().open();
        },
        _onDirectExportData() {
            // access rights check before exporting data
            return this._rpc({
                model: 'ir.exports',
                method: 'search_read',
                args: [[], ['id']],
                limit: 1,
            }).then(() => this._getExportDialogWidget().export())
        },
        _onEditGroupClicked: function (ev) {
            ev.stopPropagation();
            this.do_action({
                context: {create: false},
                type: 'ir.actions.act_window',
                views: [[false, 'form']],
                res_model: ev.data.record.model,
                res_id: ev.data.record.res_id,
                flags: {mode: 'edit'},
            });
        },
        _onFieldChanged: function (ev) {
            ev.stopPropagation();
            const recordId = ev.data.dataPointID;
    
            if (this.fieldChangedPrevented) {
                this.fieldChangedPrevented = ev;
            } else if (this.renderer.isInMultipleRecordEdition(recordId)) {
                const saveMulti = () => {
                    this.multipleRecordsSavingPromise =
                        this._saveMultipleRecords(ev.data.dataPointID, ev.target.__node, ev.data.changes);
                };
                // deal with edition of multiple lines
                ev.data.onSuccess = saveMulti; // will ask confirmation, and save
                ev.data.onFailure = saveMulti; // will show the appropriate dialog
                // disable onchanges as we'll save directly
                ev.data.notifyChange = false;
            }
            this._super.apply(this, arguments);
        },
        _onSaveLine: function (ev) {
            this.saveRecord(ev.data.recordID)
                .then(ev.data.onSuccess)
                .guardedCatch(ev.data.onFailure);
        },
        _onSelectionChanged: function (ev) {
            this.selectedRecords = ev.data.selection;
            this._toggleSidebar();
        },
        _onSetDirty: function (ev) {
            var recordId = ev.data.dataPointID;
            if (this.renderer.isInMultipleRecordEdition(recordId)) {
                ev.stopPropagation();
                Dialog.alert(this, _t("No valid record to save"), {
                    confirm_callback: async () => {
                        this.model.discardChanges(recordId);
                        await this._confirmSave(recordId);
                        this.renderer.focusCell(recordId, ev.target.__node);
                    },
                });
            } else {
                this._super.apply(this, arguments);
            }
        },
        _onToggleColumnOrder: function (ev) {
            ev.stopPropagation();
            var data = this.model.get(this.handle);
            if (!data.groupedBy) {
                this.pager.updateState({current_min: 1});
            }
            var self = this;
            this.model.setSort(data.id, ev.data.name).then(function () {
                self.update({});
            });
        },
        _onToggleGroup: function (ev) {
            ev.stopPropagation();
            var self = this;
            this.model
                .toggleGroup(ev.data.group.id)
                .then(function () {
                    self.update({}, {keepSelection: true, reload: false}).then(function () {
                        if (ev.data.onSuccess) {
                            ev.data.onSuccess();
                        }
                    });
                });
        },
    });
    
    return TimelineButtons;
    
    });
    