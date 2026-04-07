from decimal import Decimal

from django.db import models

from products.models import Product


class Shipment(models.Model):
    reference = models.CharField(max_length=100)

    # USD -> ETB
    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("155.00"),
    )

    # Costs
    insurance = models.DecimalField(max_digits=20, decimal_places=2, default=0)  # ETB
    freight_documentation = models.DecimalField(max_digits=20, decimal_places=2, default=0)  # USD

    # Local costs in ETB
    bank_lc_charge = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    inland_transport = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    storage_modjo = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    demurrage = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    loading_unloading = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    scanning = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    rent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    professional_salary = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    clearing_agent = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    miscellaneous_cost = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    custom_duty_percent = models.DecimalField(max_digits=6, decimal_places=2, default=15)

    # Calculated ETB fields
    custom_duty_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_additional_cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference

    def get_total_fob(self):
        return sum((item.unit_price or Decimal("0")) * (item.quantity or 0) for item in self.items.all())

    def get_total_fob_birr(self):
        return self.get_total_fob() * (self.exchange_rate or Decimal("0"))

    def get_insurance_birr(self):
        return self.insurance or Decimal("0")

    def get_freight_birr(self):
        return (self.freight_documentation or Decimal("0")) * (self.exchange_rate or Decimal("0"))

    def get_cif_birr(self):
        return self.get_total_fob_birr() + self.get_freight_birr() + self.get_insurance_birr()

    def get_local_costs_total(self):
        return (
            (self.bank_lc_charge or Decimal("0")) +
            (self.inland_transport or Decimal("0")) +
            (self.storage_modjo or Decimal("0")) +
            (self.demurrage or Decimal("0")) +
            (self.loading_unloading or Decimal("0")) +
            (self.scanning or Decimal("0")) +
            (self.rent or Decimal("0")) +
            (self.professional_salary or Decimal("0")) +
            (self.clearing_agent or Decimal("0")) +
            (self.miscellaneous_cost or Decimal("0"))
        )

    def recalculate_costs(self, save=True):
        cif_birr = self.get_cif_birr()

        self.custom_duty_amount = (
            (self.custom_duty_percent or Decimal("0")) / Decimal("100")
        ) * cif_birr

        self.total_additional_cost = (
            (self.custom_duty_amount or Decimal("0")) +
            self.get_freight_birr() +
            self.get_insurance_birr() +
            self.get_local_costs_total()
        )

        if save and self.pk:
            Shipment.objects.filter(pk=self.pk).update(
                custom_duty_amount=self.custom_duty_amount,
                total_additional_cost=self.total_additional_cost,
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalculate_costs(save=True)


class ShipmentItem(models.Model):
    shipment = models.ForeignKey(
        Shipment,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField(blank=True, null=True)

    unit_price = models.DecimalField(max_digits=20, decimal_places=4)  # USD

    fob_value = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    cost_share_percent = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    allocated_cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)  # ETB
    unit_landed_cost = models.DecimalField(max_digits=20, decimal_places=4, blank=True, null=True)  # ETB

    @property
    def landed_cost_total(self):
        return self.total_cost

    def get_fob_value(self):
        return (self.unit_price or Decimal("0")) * (self.quantity or 0)

    def get_fob_value_birr(self):
        return self.get_fob_value() * (self.shipment.exchange_rate or Decimal("0"))

    def get_unit_price_birr(self):
        return (self.unit_price or Decimal("0")) * (self.shipment.exchange_rate or Decimal("0"))

    def get_suggested_selling_price(self):
        if not self.unit_landed_cost:
            return Decimal("0")
        return self.unit_landed_cost * Decimal("1.30")

    def save(self, *args, **kwargs):
        if self.quantity_remaining is None:
            self.quantity_remaining = self.quantity

        self.fob_value = self.get_fob_value()
        super().save(*args, **kwargs)

        shipment = self.shipment
        shipment.recalculate_costs(save=True)

        items = shipment.items.all()
        total_fob = sum(item.get_fob_value() for item in items)

        for item in items:
            item.fob_value = item.get_fob_value()

            if total_fob > 0:
                item.cost_share_percent = (item.fob_value / total_fob) * Decimal("100")
            else:
                item.cost_share_percent = Decimal("0")

            item.allocated_cost = (
                (item.cost_share_percent / Decimal("100")) *
                (shipment.total_additional_cost or Decimal("0"))
            )

            item.total_cost = item.get_fob_value_birr() + (item.allocated_cost or Decimal("0"))
            item.unit_landed_cost = (
                item.total_cost / item.quantity if item.quantity > 0 else Decimal("0")
            )

            ShipmentItem.objects.filter(pk=item.pk).update(
                fob_value=item.fob_value,
                cost_share_percent=item.cost_share_percent,
                allocated_cost=item.allocated_cost,
                total_cost=item.total_cost,
                unit_landed_cost=item.unit_landed_cost,
                quantity_remaining=item.quantity_remaining,
            )
