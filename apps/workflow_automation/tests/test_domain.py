"""
Unit tests for the workflow_automation domain layer.

All tests use the built-in unittest module only - no Django, no I/O.
Naming convention: Given_X_When_Y_Then_Z.
"""
from __future__ import annotations

import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from apps.workflow_automation.domain.model import (
    AutomationAction,
    AutomationCondition,
    AutomationEngineService,
    AutomationRule,
    AutomationRun,
    AutomationRunLog,
    RuleEvaluationService,
)
from apps.workflow_automation.domain.value_objects import (
    ActionType,
    ConditionOperator,
    RunStatus,
    TriggerContext,
    TriggerType,
)

_UTC = timezone.utc


def _make_rule(**kwargs) -> AutomationRule:
    defaults = dict(
        id=uuid.uuid4(),
        name='Test Rule',
        trigger_type=TriggerType.DELIVERABLE_APPROVED,
        is_enabled=True,
        created_at=datetime.now(_UTC),
    )
    defaults.update(kwargs)
    return AutomationRule(**defaults)


def _make_condition(**kwargs) -> AutomationCondition:
    rule_id = uuid.uuid4()
    defaults = dict(
        id=uuid.uuid4(),
        rule_id=rule_id,
        field_name='amount',
        operator=ConditionOperator.GT,
        expected_value='100',
        position=0,
    )
    defaults.update(kwargs)
    return AutomationCondition(**defaults)


def _make_action(**kwargs) -> AutomationAction:
    defaults = dict(
        id=uuid.uuid4(),
        rule_id=uuid.uuid4(),
        action_type=ActionType.SEND_EMAIL,
        position=0,
        parameters={'to_email': 'test@example.com'},
    )
    defaults.update(kwargs)
    return AutomationAction(**defaults)


def _make_run(**kwargs) -> AutomationRun:
    defaults = dict(
        id=uuid.uuid4(),
        rule_id=uuid.uuid4(),
        trigger_type='deliverable.approved',
        status=RunStatus.PENDING,
        is_dry_run=False,
        created_at=datetime.now(_UTC),
    )
    defaults.update(kwargs)
    return AutomationRun(**defaults)


def _make_context(**kwargs) -> TriggerContext:
    defaults = dict(
        trigger_type=TriggerType.DELIVERABLE_APPROVED,
        source_id='abc-123',
        source_type='Deliverable',
        payload={'amount': '200'},
    )
    defaults.update(kwargs)
    return TriggerContext(**defaults)


class TestAutomationRuleEnableDisable(unittest.TestCase):
    def Given_enabled_rule_When_disable_Then_is_enabled_false(self):
        rule = _make_rule(is_enabled=True)
        rule.disable()
        self.assertFalse(rule.is_enabled)

    def test_Given_enabled_rule_When_disable_Then_is_enabled_false(self):
        self.Given_enabled_rule_When_disable_Then_is_enabled_false()

    def test_Given_disabled_rule_When_enable_Then_is_enabled_true(self):
        rule = _make_rule(is_enabled=False)
        rule.enable()
        self.assertTrue(rule.is_enabled)

    def test_Given_enabled_rule_When_enable_again_Then_still_true(self):
        rule = _make_rule(is_enabled=True)
        rule.enable()
        self.assertTrue(rule.is_enabled)

    def test_Given_disabled_rule_When_disable_again_Then_still_false(self):
        rule = _make_rule(is_enabled=False)
        rule.disable()
        self.assertFalse(rule.is_enabled)


class TestAutomationRuleValidation(unittest.TestCase):
    def test_Given_blank_name_When_construct_Then_raises_ValueError(self):
        with self.assertRaises(ValueError):
            _make_rule(name='')

    def test_Given_whitespace_name_When_construct_Then_raises_ValueError(self):
        with self.assertRaises(ValueError):
            _make_rule(name='   ')

    def test_Given_valid_name_When_construct_Then_no_error(self):
        rule = _make_rule(name='Valid Rule')
        self.assertEqual(rule.name, 'Valid Rule')


class TestAutomationRunLifecycle(unittest.TestCase):
    def test_Given_pending_run_When_start_Then_status_is_RUNNING(self):
        run = _make_run()
        run.start()
        self.assertEqual(run.status, RunStatus.RUNNING)

    def test_Given_pending_run_When_start_Then_started_at_is_set(self):
        run = _make_run()
        run.start()
        self.assertIsNotNone(run.started_at)

    def test_Given_running_run_When_complete_Then_status_is_SUCCESS(self):
        run = _make_run()
        run.start()
        run.complete()
        self.assertEqual(run.status, RunStatus.SUCCESS)

    def test_Given_running_run_When_complete_Then_completed_at_is_set(self):
        run = _make_run()
        run.start()
        run.complete()
        self.assertIsNotNone(run.completed_at)

    def test_Given_running_run_When_fail_Then_status_is_FAILURE(self):
        run = _make_run()
        run.start()
        run.fail()
        self.assertEqual(run.status, RunStatus.FAILURE)

    def test_Given_running_run_When_fail_Then_completed_at_is_set(self):
        run = _make_run()
        run.start()
        run.fail()
        self.assertIsNotNone(run.completed_at)

    def test_Given_dry_run_When_mark_dry_run_complete_Then_status_is_DRY_RUN(self):
        run = _make_run(is_dry_run=True)
        run.start()
        run.mark_dry_run_complete()
        self.assertEqual(run.status, RunStatus.DRY_RUN)

    def test_Given_dry_run_When_mark_dry_run_complete_Then_completed_at_is_set(self):
        run = _make_run(is_dry_run=True)
        run.start()
        run.mark_dry_run_complete()
        self.assertIsNotNone(run.completed_at)


class TestAutomationConditionValidation(unittest.TestCase):
    def test_Given_blank_field_name_When_construct_Then_raises_ValueError(self):
        with self.assertRaises(ValueError):
            _make_condition(field_name='')

    def test_Given_whitespace_field_name_When_construct_Then_raises_ValueError(self):
        with self.assertRaises(ValueError):
            _make_condition(field_name='   ')

    def test_Given_valid_field_name_When_construct_Then_no_error(self):
        condition = _make_condition(field_name='amount')
        self.assertEqual(condition.field_name, 'amount')


class TestTriggerContextImmutability(unittest.TestCase):
    def test_Given_context_When_set_attribute_Then_raises_FrozenInstanceError(self):
        context = _make_context()
        with self.assertRaises(Exception):
            context.source_id = 'new-id'  # type: ignore[misc]

    def test_Given_context_When_set_payload_Then_raises_FrozenInstanceError(self):
        context = _make_context()
        with self.assertRaises(Exception):
            context.payload = {}  # type: ignore[misc]


class TestRuleEvaluationServiceGT(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()
        self._evaluators = {
            ConditionOperator.GT.value: lambda fv, exp: float(str(fv)) > float(str(exp)),
        }

    def test_Given_gt_condition_When_value_greater_Then_returns_True(self):
        cond = _make_condition(operator=ConditionOperator.GT, expected_value='100')
        ctx = _make_context(payload={'amount': '200'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertTrue(result)

    def test_Given_gt_condition_When_value_equal_Then_returns_False(self):
        cond = _make_condition(operator=ConditionOperator.GT, expected_value='100')
        ctx = _make_context(payload={'amount': '100'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)

    def test_Given_gt_condition_When_value_less_Then_returns_False(self):
        cond = _make_condition(operator=ConditionOperator.GT, expected_value='100')
        ctx = _make_context(payload={'amount': '50'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)


class TestRuleEvaluationServiceLT(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()
        self._evaluators = {
            ConditionOperator.LT.value: lambda fv, exp: float(str(fv)) < float(str(exp)),
        }

    def test_Given_lt_condition_When_value_less_Then_returns_True(self):
        cond = _make_condition(operator=ConditionOperator.LT, expected_value='100')
        ctx = _make_context(payload={'amount': '50'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertTrue(result)

    def test_Given_lt_condition_When_value_greater_Then_returns_False(self):
        cond = _make_condition(operator=ConditionOperator.LT, expected_value='100')
        ctx = _make_context(payload={'amount': '200'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)


class TestRuleEvaluationServiceEQ(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()
        self._evaluators = {
            ConditionOperator.EQ.value: lambda fv, exp: str(fv) == str(exp),
        }

    def test_Given_eq_condition_When_values_equal_Then_returns_True(self):
        cond = _make_condition(
            field_name='status', operator=ConditionOperator.EQ, expected_value='APPROVED'
        )
        ctx = _make_context(payload={'status': 'APPROVED'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertTrue(result)

    def test_Given_eq_condition_When_values_differ_Then_returns_False(self):
        cond = _make_condition(
            field_name='status', operator=ConditionOperator.EQ, expected_value='APPROVED'
        )
        ctx = _make_context(payload={'status': 'PENDING'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)


class TestRuleEvaluationServiceCONTAINS(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()
        self._evaluators = {
            ConditionOperator.CONTAINS.value: lambda fv, exp: str(exp) in str(fv),
        }

    def test_Given_contains_condition_When_substring_present_Then_returns_True(self):
        cond = _make_condition(
            field_name='note', operator=ConditionOperator.CONTAINS, expected_value='urgent'
        )
        ctx = _make_context(payload={'note': 'This is urgent!'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertTrue(result)

    def test_Given_contains_condition_When_substring_absent_Then_returns_False(self):
        cond = _make_condition(
            field_name='note', operator=ConditionOperator.CONTAINS, expected_value='urgent'
        )
        ctx = _make_context(payload={'note': 'Routine check'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)


class TestRuleEvaluationServiceASSIGNED_TO(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()
        self._evaluators = {
            ConditionOperator.ASSIGNED_TO.value: lambda fv, exp: str(fv) == str(exp),
        }

    def test_Given_assigned_to_condition_When_matches_Then_returns_True(self):
        cond = _make_condition(
            field_name='assignee', operator=ConditionOperator.ASSIGNED_TO, expected_value='user-1'
        )
        ctx = _make_context(payload={'assignee': 'user-1'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertTrue(result)

    def test_Given_assigned_to_condition_When_no_match_Then_returns_False(self):
        cond = _make_condition(
            field_name='assignee', operator=ConditionOperator.ASSIGNED_TO, expected_value='user-1'
        )
        ctx = _make_context(payload={'assignee': 'user-2'})
        result = self._service.evaluate(self._rule, [cond], ctx, self._evaluators)
        self.assertFalse(result)


class TestRuleEvaluationServiceEdgeCases(unittest.TestCase):
    def setUp(self):
        self._service = RuleEvaluationService()
        self._rule = _make_rule()

    def test_Given_no_conditions_When_evaluate_Then_returns_True(self):
        ctx = _make_context()
        result = self._service.evaluate(self._rule, [], ctx, {})
        self.assertTrue(result)

    def test_Given_unknown_operator_When_evaluate_Then_returns_False(self):
        cond = _make_condition(operator=ConditionOperator.GT, expected_value='100')
        ctx = _make_context(payload={'amount': '200'})
        # Pass empty evaluators so operator is unknown
        result = self._service.evaluate(self._rule, [cond], ctx, {})
        self.assertFalse(result)

    def test_Given_two_conditions_When_first_fails_Then_short_circuits(self):
        evaluator_call_count = [0]

        def counting_evaluator(fv, exp):
            evaluator_call_count[0] += 1
            return False

        cond1 = _make_condition(
            field_name='a', operator=ConditionOperator.EQ, expected_value='x'
        )
        cond2 = _make_condition(
            field_name='b', operator=ConditionOperator.EQ, expected_value='y'
        )
        ctx = _make_context(payload={'a': 'z', 'b': 'y'})
        evaluators = {ConditionOperator.EQ.value: counting_evaluator}
        result = self._service.evaluate(self._rule, [cond1, cond2], ctx, evaluators)

        self.assertFalse(result)
        self.assertEqual(evaluator_call_count[0], 1)


class TestAutomationEngineServiceConditionsPassing(unittest.TestCase):
    def test_Given_conditions_pass_When_execute_Then_run_status_SUCCESS(self):
        rule = _make_rule()
        condition = _make_condition(
            rule_id=rule.id, operator=ConditionOperator.EQ, expected_value='yes'
        )
        action = _make_action(rule_id=rule.id, action_type=ActionType.UPDATE_STATUS)
        run = _make_run(rule_id=rule.id)
        ctx = _make_context(payload={condition.field_name: 'yes'})

        handler_called = [False]

        def mock_handler(params, context):
            handler_called[0] = True
            return 'ok'

        condition_evaluators = {ConditionOperator.EQ.value: lambda fv, exp: str(fv) == str(exp)}
        action_handlers = {ActionType.UPDATE_STATUS.value: mock_handler}

        log_factory = MagicMock()
        service = AutomationEngineService()
        result = service.execute(
            rule, [condition], [action], ctx,
            condition_evaluators, action_handlers, run, log_factory,
        )

        self.assertEqual(result.status, RunStatus.SUCCESS)
        self.assertTrue(handler_called[0])

    def test_Given_conditions_pass_When_execute_Then_action_handler_called(self):
        rule = _make_rule()
        action = _make_action(rule_id=rule.id)
        run = _make_run(rule_id=rule.id)
        ctx = _make_context()

        received_params = {}

        def mock_handler(params, context):
            received_params.update(params)

        action_handlers = {ActionType.SEND_EMAIL.value: mock_handler}
        service = AutomationEngineService()
        service.execute(rule, [], [action], ctx, {}, action_handlers, run, MagicMock())

        self.assertEqual(received_params.get('to_email'), 'test@example.com')


class TestAutomationEngineServiceConditionsFailing(unittest.TestCase):
    def test_Given_conditions_fail_When_execute_Then_run_status_FAILURE(self):
        rule = _make_rule()
        condition = _make_condition(
            rule_id=rule.id, operator=ConditionOperator.EQ, expected_value='yes'
        )
        run = _make_run(rule_id=rule.id)
        ctx = _make_context(payload={condition.field_name: 'no'})

        evaluators = {ConditionOperator.EQ.value: lambda fv, exp: str(fv) == str(exp)}
        service = AutomationEngineService()
        result = service.execute(rule, [condition], [], ctx, evaluators, {}, run, MagicMock())

        self.assertEqual(result.status, RunStatus.FAILURE)


class TestAutomationEngineServiceDryRun(unittest.TestCase):
    def test_Given_dry_run_When_conditions_pass_Then_actions_not_dispatched(self):
        rule = _make_rule()
        action = _make_action(rule_id=rule.id)
        run = _make_run(rule_id=rule.id, is_dry_run=True)
        ctx = _make_context()

        handler_called = [False]

        def mock_handler(params, context):
            handler_called[0] = True

        action_handlers = {ActionType.SEND_EMAIL.value: mock_handler}
        service = AutomationEngineService()
        result = service.execute(rule, [], [action], ctx, {}, action_handlers, run, MagicMock())

        self.assertEqual(result.status, RunStatus.DRY_RUN)
        self.assertFalse(handler_called[0])


class TestAutomationEngineServiceActionException(unittest.TestCase):
    def test_Given_action_raises_When_execute_Then_run_status_FAILURE(self):
        rule = _make_rule()
        action = _make_action(rule_id=rule.id)
        run = _make_run(rule_id=rule.id)
        ctx = _make_context()

        def failing_handler(params, context):
            raise RuntimeError('simulated failure')

        action_handlers = {ActionType.SEND_EMAIL.value: failing_handler}
        log_factory = MagicMock()
        service = AutomationEngineService()
        result = service.execute(rule, [], [action], ctx, {}, action_handlers, run, log_factory)

        self.assertEqual(result.status, RunStatus.FAILURE)

    def test_Given_action_raises_When_execute_Then_run_log_created(self):
        rule = _make_rule()
        action = _make_action(rule_id=rule.id)
        run = _make_run(rule_id=rule.id)
        ctx = _make_context()

        def failing_handler(params, context):
            raise RuntimeError('boom')

        action_handlers = {ActionType.SEND_EMAIL.value: failing_handler}
        log_factory = MagicMock()
        service = AutomationEngineService()
        service.execute(rule, [], [action], ctx, {}, action_handlers, run, log_factory)

        log_factory.assert_called()


class TestValueObjectEnums(unittest.TestCase):
    def test_TriggerType_has_deliverable_approved(self):
        self.assertEqual(TriggerType.DELIVERABLE_APPROVED.value, 'deliverable.approved')

    def test_TriggerType_has_invoice_overdue(self):
        self.assertEqual(TriggerType.INVOICE_OVERDUE.value, 'invoice.overdue')

    def test_TriggerType_has_metric_threshold_crossed(self):
        self.assertEqual(TriggerType.METRIC_THRESHOLD_CROSSED.value, 'metric.threshold_crossed')

    def test_TriggerType_has_file_uploaded(self):
        self.assertEqual(TriggerType.FILE_UPLOADED.value, 'file.uploaded')

    def test_ConditionOperator_all_five_values(self):
        values = {op.value for op in ConditionOperator}
        self.assertSetEqual(values, {'gt', 'lt', 'eq', 'contains', 'assigned_to'})

    def test_ActionType_has_send_email(self):
        self.assertEqual(ActionType.SEND_EMAIL.value, 'send_email')

    def test_ActionType_has_send_sms(self):
        self.assertEqual(ActionType.SEND_SMS.value, 'send_sms')

    def test_ActionType_has_create_activity_event(self):
        self.assertEqual(ActionType.CREATE_ACTIVITY_EVENT.value, 'create_activity_event')

    def test_ActionType_has_update_status(self):
        self.assertEqual(ActionType.UPDATE_STATUS.value, 'update_status')

    def test_RunStatus_has_all_five_values(self):
        values = {s.value for s in RunStatus}
        self.assertSetEqual(values, {'pending', 'running', 'success', 'failure', 'dry_run'})

    def test_RunStatus_PENDING_value(self):
        self.assertEqual(RunStatus.PENDING.value, 'pending')

    def test_RunStatus_RUNNING_value(self):
        self.assertEqual(RunStatus.RUNNING.value, 'running')

    def test_RunStatus_SUCCESS_value(self):
        self.assertEqual(RunStatus.SUCCESS.value, 'success')

    def test_RunStatus_FAILURE_value(self):
        self.assertEqual(RunStatus.FAILURE.value, 'failure')

    def test_RunStatus_DRY_RUN_value(self):
        self.assertEqual(RunStatus.DRY_RUN.value, 'dry_run')


if __name__ == '__main__':
    unittest.main()
