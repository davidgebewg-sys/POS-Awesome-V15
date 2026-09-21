<template>
	<section
		class="exchange-panel"
		:class="[`exchange-panel--${stage}`, { 'exchange-panel--compact': compact }]"
		data-testid="exchange-status-panel"
	>
		<div class="exchange-panel__marker" aria-hidden="true">
			<v-icon :icon="stage === 'return' ? 'mdi-package-variant-closed-remove' : 'mdi-swap-horizontal-bold'" />
		</div>
		<div class="exchange-panel__copy">
			<span class="exchange-panel__eyebrow">{{ __("Item exchange") }}</span>
			<strong>
				{{
					stage === "return"
						? __("Choose the items coming back")
						: __("Add replacement items")
				}}
			</strong>
			<span class="exchange-panel__detail">
				<template v-if="stage === 'return'">
					{{ __("Remove anything the customer is keeping, then continue.") }}
				</template>
				<template v-else>
					{{ __("Return credit") }}:
					<b>{{ currencySymbol }}{{ formatAmount(returnTotal) }}</b>
					<span class="exchange-panel__dot" aria-hidden="true">&middot;</span>
					{{ settlementLabel }}:
					<b>{{ currencySymbol }}{{ formatAmount(Math.abs(difference)) }}</b>
				</template>
			</span>
		</div>
		<div class="exchange-panel__actions">
			<v-btn variant="text" color="medium-emphasis" size="small" @click="$emit('cancel')">
				{{ __("Cancel exchange") }}
			</v-btn>
			<v-btn
				v-if="stage === 'return'"
				color="primary"
				variant="flat"
				prepend-icon="mdi-arrow-right"
				:loading="continuing"
				@click="$emit('continue')"
			>
				{{ __("Choose replacement") }}
			</v-btn>
		</div>
	</section>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps({
	stage: { type: String, default: "return" },
	returnTotal: { type: Number, default: 0 },
	saleTotal: { type: Number, default: 0 },
	currencySymbol: { type: String, default: "" },
	formatAmount: { type: Function, required: true },
	continuing: { type: Boolean, default: false },
	compact: { type: Boolean, default: false },
});

defineEmits(["continue", "cancel"]);

const difference = computed(() => Number(props.saleTotal || 0) - Number(props.returnTotal || 0));
const settlementLabel = computed(() =>
	difference.value >= 0 ? __("Customer pays") : __("Customer credit"),
);
</script>

<style scoped>
.exchange-panel {
	display: grid;
	grid-template-columns: auto minmax(0, 1fr) auto;
	align-items: center;
	gap: 14px;
	margin: 12px 12px 0;
	padding: 14px 16px;
	border: 1px solid color-mix(in srgb, rgb(var(--v-theme-primary)) 32%, transparent);
	border-radius: 14px;
	background:
		linear-gradient(105deg, color-mix(in srgb, rgb(var(--v-theme-primary)) 12%, transparent), transparent 58%),
		rgb(var(--v-theme-surface));
	box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.exchange-panel--sale {
	border-color: color-mix(in srgb, rgb(var(--v-theme-success)) 36%, transparent);
	background:
		linear-gradient(105deg, color-mix(in srgb, rgb(var(--v-theme-success)) 13%, transparent), transparent 58%),
		rgb(var(--v-theme-surface));
}

.exchange-panel__marker {
	display: grid;
	place-items: center;
	width: 42px;
	height: 42px;
	border-radius: 12px;
	color: rgb(var(--v-theme-on-primary));
	background: rgb(var(--v-theme-primary));
}

.exchange-panel--sale .exchange-panel__marker {
	background: rgb(var(--v-theme-success));
}

.exchange-panel__copy {
	display: grid;
	gap: 2px;
	min-width: 0;
}

.exchange-panel__eyebrow {
	font-size: 0.68rem;
	font-weight: 800;
	letter-spacing: 0.12em;
	text-transform: uppercase;
	color: rgb(var(--v-theme-primary));
}

.exchange-panel__detail {
	font-size: 0.82rem;
	color: rgb(var(--v-theme-on-surface-variant));
}

.exchange-panel__dot {
	padding-inline: 6px;
}

.exchange-panel__actions {
	display: flex;
	align-items: center;
	gap: 8px;
}

.exchange-panel--compact {
	margin: 10px 0 0;
	padding: 10px 12px;
	border-radius: 12px;
	box-shadow: none;
}

.exchange-panel--compact .exchange-panel__marker {
	width: 36px;
	height: 36px;
	border-radius: 10px;
}

.exchange-panel--compact .exchange-panel__copy {
	line-height: 1.2;
}

@media (max-width: 760px) {
	.exchange-panel {
		grid-template-columns: auto minmax(0, 1fr);
	}

	.exchange-panel__actions {
		grid-column: 1 / -1;
		justify-content: flex-end;
	}
}
</style>
