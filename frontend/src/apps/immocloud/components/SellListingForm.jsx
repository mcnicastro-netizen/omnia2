/* OMNIA — B2C sell listing form (MOVE-ONLY from SellPage). */
import React from "react";
import { useTranslation } from "react-i18next";
import AlImproveButton from "../../../shared/components/AlImproveButton";
import PhotoUploader from "../../immoweb/components/PhotoUploader";
import { ENERGY_CLASS_OPTIONS } from "../../../shared/lib/energyClasses";
import AddressAutocomplete from "./AddressAutocomplete";
import B2CStagingPanel from "./B2CStagingPanel";
import B2CVideoTourPanel from "./B2CVideoTourPanel";
import { onInvalidItalian, onInputClearCustomValidity } from "../../../shared/lib/itHtmlValidity";
import {
  B2C_FEATURES,
  B2C_MAX_PHOTOS,
  CITY_SUGGESTIONS,
  CONDITIONS,
  HEATING,
  PROPERTY_TYPES,
} from "./sellConstants";
import { halDescriptionReady } from "./sellPayload";
import { Field, FloorPlanUploader, inputCls } from "./SellFormPrimitives";

export default function SellListingForm({
  form,
  setForm,
  editing,
  busy,
  user,
  save,
  onCancel,
  stagingBusy,
}) {
  const { t } = useTranslation();
  if (!form) return null;
  return (
      <form
        data-testid="sell-form"
        onSubmit={save}
        onInvalid={onInvalidItalian}
        onInput={onInputClearCustomValidity}
        className="bg-white border border-stone-200 rounded-lg p-6 space-y-4"
      >
        <h2 className="text-xl font-light mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {editing ? t("cloud.sell.form_edit_title") : t("cloud.sell.form_new_title")}
        </h2>

        {/* 1 · Titolo */}
        <Field label={t("cloud.sell.f_title")} required>
          <input data-testid="sell-f-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
            required minLength={3} maxLength={200} className={inputCls} />
        </Field>

        {/* 2 · Descrizione */}
        <Field label={t("cloud.sell.f_description")}>
          <div className="space-y-2">
            <p className="text-xs text-stone-500">{t("cloud.sell.f_description_hal_hint")}</p>
            <textarea data-testid="sell-f-description" rows={4} maxLength={10000}
              value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className={inputCls} />
            <div className="flex justify-end">
              <AlImproveButton
                field="description"
                value={form.description}
                propertyData={form}
                onApply={(text) => setForm({ ...form, description: text })}
                testId="sell-al-improve-description"
                ready={halDescriptionReady(form)}
                notReadyMessage={t("cloud.sell.hal_need_fields")}
              />
            </div>
          </div>
        </Field>

        {/* 3 · Foto + video tour */}
        <Field label={t("cloud.sell.f_photos")}>
          <p className="text-xs text-stone-500 mb-2">{t("cloud.sell.f_photos_hint")}</p>
          <PhotoUploader
            photos={form.photos || []}
            onChange={(photos) => setForm((f) => ({ ...f, photos }))}
            max={B2C_MAX_PHOTOS}
            uploadUrl={B2C_MEDIA_UPLOAD}
            uploadExtraFields={{ kind: "photo" }}
          />
          <B2CVideoTourPanel
            listingId={editing?.id || null}
            photoCount={(form.photos || []).length}
            onError={(msg) => setError(msg)}
            testIdPrefix="sell-video"
          />
        </Field>

        {/* 4 · Virtual staging (scegli foto da modificare) */}
        <div data-testid="sell-staging-block">
          {editing?.id ? (
            <B2CStagingPanel
              listingId={editing.id}
              photos={form.photos || []}
              busy={stagingBusy}
              setBusy={setStagingBusy}
              onStatus={setStagingStatus}
              onError={setError}
              onEnsurePhotosSaved={async () => {
                const payload = buildListingPayload(form);
                if (!payload.photos.length) {
                  const err = new Error("listing_has_no_photos");
                  err.response = {
                    data: {
                      detail: {
                        error: "listing_has_no_photos",
                        code: "listing_has_no_photos",
                        message:
                          "Carica almeno una foto e aspetta che finisca l'upload prima dello staging.",
                      },
                    },
                  };
                  throw err;
                }
                await api.patch(`/cloud/me/properties/${editing.id}`, {
                  photos: payload.photos,
                  floor_plan_url: payload.floor_plan_url || null,
                });
              }}
              onPaidAttached={async () => {
                const items = await reloadListings().catch(() => []);
                const fresh = (items || []).find((x) => x.id === editing.id);
                if (fresh?.photos) setForm((f) => ({ ...f, photos: fresh.photos }));
              }}
              testIdPrefix="sell-staging"
            />
          ) : (
            <p className="text-[11px] text-stone-500" data-testid="sell-staging-hint">
              {t("cloud.sell.staging_need_listing")}
            </p>
          )}
        </div>

        <Field label={t("cloud.sell.f_floor_plan")}>
          <p className="text-xs text-stone-500 mb-2">{t("cloud.sell.f_floor_plan_hint")}</p>
          <FloorPlanUploader
            url={form.floor_plan_url}
            onChange={(url) => setForm({ ...form, floor_plan_url: url || "" })}
          />
        </Field>

        {/* 5 · Dettagli immobile + contatto */}
        <div
          data-testid="sell-options-block"
          className="space-y-4 pt-2 border-t border-stone-100"
        >
          <p className="text-[10px] uppercase tracking-[0.22em] text-stone-500">
            {t("cloud.sell.options_section", "Dettagli e opzioni")}
          </p>

        <div className="grid grid-cols-2 gap-3">
          <Field label={t("cloud.sell.f_type")}>
            <select data-testid="sell-f-type" value={form.property_type} onChange={(e) => setForm({ ...form, property_type: e.target.value })} className={inputCls}>
              {PROPERTY_TYPES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </Field>
          <Field label={t("cloud.sell.f_operation")}>
            <select data-testid="sell-f-operation" value={form.operation} onChange={(e) => setForm({ ...form, operation: e.target.value })} className={inputCls}>
              <option value="sale">{t("cloud.sell.op_sale")}</option>
              <option value="rent">{t("cloud.sell.op_rent")}</option>
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label={t("cloud.sell.f_city")} required>
            <input
              data-testid="sell-f-city"
              value={form.city}
              required
              list="sell-city-suggest"
              autoComplete="address-level2"
              placeholder={t("cloud.sell.f_city_ph")}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className={inputCls}
            />
            <datalist id="sell-city-suggest">
              {CITY_SUGGESTIONS.map((c) => (
                <option key={c} value={c} />
              ))}
            </datalist>
          </Field>
          <Field label={t("cloud.sell.f_postal")}>
            <input data-testid="sell-f-postal" value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} className={inputCls} />
          </Field>
        </div>

        <Field label={t("cloud.sell.f_zone")}>
          <input data-testid="sell-f-zone" value={form.zone} onChange={(e) => setForm({ ...form, zone: e.target.value })} className={inputCls} placeholder={t("cloud.sell.f_zone_ph")} />
        </Field>

        <div className="grid grid-cols-3 gap-3">
          <div className="col-span-2">
            <Field label={t("cloud.sell.f_address")}>
              <AddressAutocomplete
                testid="sell-f-address"
                value={form.address}
                onChange={(text) => setForm((f) => ({ ...f, address: text }))}
                onSelect={(rec) => {
                  const road =
                    (rec.road || "").trim() ||
                    String(rec.normalized || "")
                      .split(",")[0]
                      .trim() ||
                    rec.normalized;
                  setForm((f) => ({
                    ...f,
                    address: road || f.address,
                    city: (f.city || "").trim() ? f.city : (rec.comune || f.city),
                    postal_code: (f.postal_code || "").trim()
                      ? f.postal_code
                      : (rec.cap || f.postal_code),
                    zone: (f.zone || "").trim() ? f.zone : (rec.zone || f.zone),
                  }));
                }}
                placeholder={t("cloud.sell.f_address_ph")}
                inputClassName={inputCls}
              />
            </Field>
          </div>
          <Field label={t("cloud.sell.f_street_number")}>
            <input
              data-testid="sell-f-street-number"
              value={form.street_number}
              onChange={(e) => setForm({ ...form, street_number: e.target.value })}
              className={inputCls}
              placeholder={t("cloud.sell.f_street_number_ph")}
            />
          </Field>
        </div>
        <p className="text-[11px] text-stone-500 -mt-2">{t("cloud.sell.f_street_number_hint")}</p>

        <div className="grid grid-cols-2 gap-3">
          {form.operation === "sale" ? (
            <Field label={t("cloud.sell.f_price")}>
              <input data-testid="sell-f-price" type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className={inputCls} />
            </Field>
          ) : (
            <Field label={t("cloud.sell.f_rent")}>
              <input data-testid="sell-f-rent" type="number" min="0" value={form.rent_monthly} onChange={(e) => setForm({ ...form, rent_monthly: e.target.value })} className={inputCls} />
            </Field>
          )}
          <Field label={t("cloud.sell.f_surface")}>
            <input data-testid="sell-f-surface" type="number" min="0" value={form.surface_sqm} onChange={(e) => setForm({ ...form, surface_sqm: e.target.value })} className={inputCls} />
          </Field>
        </div>

        <Field label={t("cloud.sell.f_condo_fees")}>
          <input data-testid="sell-f-condo-fees" type="number" min="0" value={form.condo_fees} onChange={(e) => setForm({ ...form, condo_fees: e.target.value })} className={inputCls} />
        </Field>

        <div className="grid grid-cols-3 gap-3">
          <Field label={t("cloud.sell.f_rooms")}>
            <input data-testid="sell-f-rooms" type="number" min="0" value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} className={inputCls} />
          </Field>
          <Field label={t("cloud.sell.f_bedrooms")}>
            <input data-testid="sell-f-bedrooms" type="number" min="0" value={form.bedrooms} onChange={(e) => setForm({ ...form, bedrooms: e.target.value })} className={inputCls} />
          </Field>
          <Field label={t("cloud.sell.f_bathrooms")}>
            <input data-testid="sell-f-bathrooms" type="number" min="0" value={form.bathrooms} onChange={(e) => setForm({ ...form, bathrooms: e.target.value })} className={inputCls} />
          </Field>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Field label={t("cloud.sell.f_floor")}>
            <input data-testid="sell-f-floor" type="number" value={form.floor} onChange={(e) => setForm({ ...form, floor: e.target.value })} className={inputCls} />
          </Field>
          <Field label={t("cloud.sell.f_total_floors")}>
            <input data-testid="sell-f-total-floors" type="number" min="0" value={form.total_floors} onChange={(e) => setForm({ ...form, total_floors: e.target.value })} className={inputCls} />
          </Field>
          <Field label={t("cloud.sell.f_year_built")}>
            <input data-testid="sell-f-year" type="number" min="1800" max="2100" value={form.year_built} onChange={(e) => setForm({ ...form, year_built: e.target.value })} className={inputCls} />
          </Field>
          <Field label={t("cloud.sell.f_condition")}>
            <select data-testid="sell-f-condition" value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })} className={inputCls}>
              <option value="">—</option>
              {CONDITIONS.map((c) => (
                <option key={c} value={c}>{t(`cloud.sell.condition_${c}`)}</option>
              ))}
            </select>
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label={t("cloud.sell.f_energy")}>
            <select
              data-testid="sell-f-energy"
              value={form.energy.energy_class}
              onChange={(e) => setForm({ ...form, energy: { ...form.energy, energy_class: e.target.value } })}
              className={inputCls}
            >
              <option value="">—</option>
              {ENERGY_CLASS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </Field>
          <Field label={t("cloud.sell.f_heating")}>
            <select
              data-testid="sell-f-heating"
              value={form.energy.heating}
              onChange={(e) => setForm({ ...form, energy: { ...form.energy, heating: e.target.value } })}
              className={inputCls}
            >
              <option value="">—</option>
              {HEATING.map((h) => (
                <option key={h} value={h}>{t(`cloud.sell.heating_${h}`)}</option>
              ))}
            </select>
          </Field>
        </div>

        <fieldset data-testid="sell-features" className="border border-stone-200 rounded-xl p-4">
          <legend className="text-[10px] uppercase tracking-widest text-stone-500 px-1">{t("cloud.sell.f_features")}</legend>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
            {B2C_FEATURES.map((k) => (
              <label key={k} className="flex items-center gap-2 text-sm text-stone-700 cursor-pointer">
                <input
                  type="checkbox"
                  data-testid={`sell-feat-${k}`}
                  checked={!!form.features[k]}
                  onChange={(e) => setForm({
                    ...form,
                    features: { ...form.features, [k]: e.target.checked },
                  })}
                  className="h-4 w-4 rounded border-stone-300 text-[#0B1E3F]"
                />
                {t(`cloud.sell.feat_${k}`)}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset
          data-testid="sell-contact-channels"
          className="relative overflow-hidden rounded-2xl border border-stone-200/80 bg-gradient-to-br from-[#fbf8f3] to-white p-5 space-y-4"
        >
          <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[#C19A6B]/10" aria-hidden />
          <div>
            <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-1">
              {t("cloud.sell.f_contact_legend")}
            </p>
            <p className="text-sm text-[#0B1E3F] leading-relaxed" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("cloud.sell.f_contact_hint")}
            </p>
          </div>
          <Field label={t("cloud.sell.f_contact_name")}>
            <input
              data-testid="sell-f-contact-name"
              value={form.contact_display_name}
              onChange={(e) => setForm({ ...form, contact_display_name: e.target.value })}
              className={inputCls}
              placeholder={user?.name?.split?.(" ")?.[0] || ""}
            />
          </Field>
          <div className="grid gap-2">
            {[
              { key: "contact_show_email", testid: "sell-f-show-email", label: t("cloud.sell.f_show_email") },
              { key: "contact_show_phone", testid: "sell-f-show-phone", label: t("cloud.sell.f_show_phone") },
              { key: "contact_show_whatsapp", testid: "sell-f-show-whatsapp", label: t("cloud.sell.f_show_whatsapp") },
            ].map((opt) => (
              <label
                key={opt.key}
                className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm cursor-pointer transition ${
                  form[opt.key]
                    ? "border-[#C19A6B]/50 bg-[#C19A6B]/10 text-[#0B1E3F]"
                    : "border-stone-200 bg-white/70 text-stone-700 hover:border-stone-300"
                }`}
              >
                <input
                  type="checkbox"
                  data-testid={opt.testid}
                  checked={form[opt.key]}
                  onChange={(e) => setForm({ ...form, [opt.key]: e.target.checked })}
                  className="h-4 w-4 rounded border-stone-300 text-[#0B1E3F] focus:ring-[#C19A6B]"
                />
                {opt.label}
              </label>
            ))}
          </div>
          {form.contact_show_phone && (
            <Field label={t("cloud.sell.f_phone")}>
              <input
                data-testid="sell-f-phone"
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className={inputCls}
                placeholder="+39…"
              />
            </Field>
          )}
          {form.contact_show_whatsapp && (
            <Field label={t("cloud.sell.f_whatsapp")}>
              <input
                data-testid="sell-f-whatsapp"
                value={form.contact_whatsapp}
                onChange={(e) => setForm({ ...form, contact_whatsapp: e.target.value })}
                className={inputCls}
                placeholder="+39…"
              />
            </Field>
          )}
        </fieldset>
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={busy} data-testid="sell-save-btn"
            className="px-6 py-2.5 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded-lg hover:bg-[#C19A6B] transition disabled:opacity-50">
            {busy ? t("common.saving") : t("common.save")}
          </button>
          <button type="button" onClick={onCancel}
              className="px-6 py-2.5 border border-stone-300 text-sm uppercase tracking-widest rounded-lg hover:bg-stone-50">
              {t("common.cancel")}
            </button>
        </div>
      </form>

  );
}
