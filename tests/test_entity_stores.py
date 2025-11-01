"""Tests for Entity Management System."""

import json

import pytest

from mcp.core.entities import (
    OEM,
    ContractVehicle,
    ContractVehicleStore,
    Customer,
    CustomerStore,
    Distributor,
    DistributorStore,
    OEMStore,
    Partner,
    PartnerStore,
    Region,
    RegionStore,
)


class TestOEMStore:
    """Tests for OEM entity store."""

    @pytest.fixture
    def oem_store(self, tmp_path):
        """Create temporary OEM store."""
        storage_path = tmp_path / "oems.json"
        return OEMStore(str(storage_path))

    def test_add_oem(self, oem_store):
        """Test adding a new OEM."""
        oem = OEM(
            id="microsoft",
            name="Microsoft",
            tier="Strategic",
            programs=["Azure", "M365"],
        )

        added = oem_store.add(oem)

        assert added.id == "microsoft"
        assert added.name == "Microsoft"
        assert added.tier == "Strategic"
        assert added.active is True
        assert oem_store.count() == 1

    def test_get_oem(self, oem_store):
        """Test retrieving OEM by ID."""
        oem = OEM(id="cisco", name="Cisco", tier="Strategic")
        oem_store.add(oem)

        retrieved = oem_store.get("cisco")

        assert retrieved is not None
        assert retrieved.id == "cisco"
        assert retrieved.name == "Cisco"

    def test_get_by_name(self, oem_store):
        """Test retrieving OEM by name (case-insensitive)."""
        oem = OEM(id="dell", name="Dell", tier="Gold")
        oem_store.add(oem)

        retrieved = oem_store.get_by_name("dell")
        assert retrieved is not None
        assert retrieved.id == "dell"

        # Case insensitive
        retrieved_upper = oem_store.get_by_name("DELL")
        assert retrieved_upper is not None
        assert retrieved_upper.id == "dell"

    def test_update_oem(self, oem_store):
        """Test updating an OEM."""
        oem = OEM(id="hpe", name="HPE", tier="Gold")
        oem_store.add(oem)

        # Update tier
        updated_oem = OEM(id="hpe", name="HPE", tier="Strategic", programs=["GreenLake"])
        oem_store.update("hpe", updated_oem)

        retrieved = oem_store.get("hpe")
        assert retrieved.tier == "Strategic"
        assert "GreenLake" in retrieved.programs

    def test_delete_oem_soft(self, oem_store):
        """Test soft delete (mark inactive)."""
        oem = OEM(id="vmware", name="VMware", tier="Gold")
        oem_store.add(oem)

        result = oem_store.delete("vmware")

        assert result is True
        retrieved = oem_store.get("vmware")
        assert retrieved is not None
        assert retrieved.active is False

        # Should not appear in active-only queries
        active_oems = oem_store.get_all(active_only=True)
        assert len(active_oems) == 0

    def test_hard_delete_oem(self, oem_store):
        """Test hard delete (permanent removal)."""
        oem = OEM(id="netapp", name="NetApp", tier="Gold")
        oem_store.add(oem)

        result = oem_store.hard_delete("netapp")

        assert result is True
        retrieved = oem_store.get("netapp")
        assert retrieved is None
        assert oem_store.count() == 0

    def test_duplicate_id_error(self, oem_store):
        """Test error when adding duplicate ID."""
        oem1 = OEM(id="oracle", name="Oracle", tier="Silver")
        oem_store.add(oem1)

        oem2 = OEM(id="oracle", name="Oracle Cloud", tier="Gold")
        with pytest.raises(ValueError, match="already exists"):
            oem_store.add(oem2)

    def test_persistence(self, tmp_path):
        """Test data persists across store instances."""
        storage_path = tmp_path / "oems.json"

        # Create and populate store
        store1 = OEMStore(str(storage_path))
        oem = OEM(id="aws", name="AWS", tier="Silver")
        store1.add(oem)

        # Create new store instance from same file
        store2 = OEMStore(str(storage_path))

        assert store2.count() == 1
        retrieved = store2.get("aws")
        assert retrieved is not None
        assert retrieved.name == "AWS"


class TestRegionStore:
    """Tests for Region entity store."""

    @pytest.fixture
    def region_store(self, tmp_path):
        """Create temporary Region store."""
        storage_path = tmp_path / "regions.json"
        return RegionStore(str(storage_path))

    def test_add_region(self, region_store):
        """Test adding a region."""
        region = Region(id="east", name="East", bonus=2.5)
        added = region_store.add(region)

        assert added.id == "east"
        assert added.bonus == 2.5

    def test_get_bonus(self, region_store):
        """Test getting region bonus."""
        region = Region(id="west", name="West", bonus=2.0)
        region_store.add(region)

        bonus = region_store.get_bonus("West")
        assert bonus == 2.0

    def test_get_bonus_inactive(self, region_store):
        """Test getting bonus for inactive region returns 0."""
        region = Region(id="central", name="Central", bonus=1.5)
        region_store.add(region)
        region_store.delete("central")

        bonus = region_store.get_bonus("Central")
        assert bonus == 0.0

    def test_get_bonus_not_found(self, region_store):
        """Test getting bonus for non-existent region returns 0."""
        bonus = region_store.get_bonus("Unknown")
        assert bonus == 0.0


class TestContractVehicleStore:
    """Tests for Contract Vehicle entity store."""

    @pytest.fixture
    def cv_store(self, tmp_path):
        """Create temporary CV store."""
        storage_path = tmp_path / "contract_vehicles.json"
        return ContractVehicleStore(str(storage_path))

    def test_add_contract_vehicle(self, cv_store):
        """Test adding a contract vehicle."""
        cv = ContractVehicle(
            id="sewp-v",
            name="SEWP V",
            priority_score=95.0,
            oems_supported=["microsoft", "cisco"],
            categories=["IT Hardware", "Software"],
        )
        added = cv_store.add(cv)

        assert added.id == "sewp-v"
        assert added.priority_score == 95.0
        assert len(added.oems_supported) == 2

    def test_get_by_oem(self, cv_store):
        """Test getting CVs by OEM."""
        cv1 = ContractVehicle(
            id="sewp-v",
            name="SEWP V",
            priority_score=95.0,
            oems_supported=["microsoft", "cisco"],
        )
        cv2 = ContractVehicle(
            id="gsa",
            name="GSA Schedule",
            priority_score=90.0,
            oems_supported=["microsoft", "dell"],
        )
        cv_store.add(cv1)
        cv_store.add(cv2)

        microsoft_cvs = cv_store.get_by_oem("microsoft")
        assert len(microsoft_cvs) == 2

        cisco_cvs = cv_store.get_by_oem("cisco")
        assert len(cisco_cvs) == 1
        assert cisco_cvs[0].id == "sewp-v"

    def test_get_by_category(self, cv_store):
        """Test getting CVs by category."""
        cv1 = ContractVehicle(
            id="sewp-v",
            name="SEWP V",
            priority_score=95.0,
            categories=["IT Hardware", "Software"],
        )
        cv2 = ContractVehicle(
            id="cio-sp3",
            name="CIO-SP3",
            priority_score=85.0,
            categories=["IT Services", "Cloud"],
        )
        cv_store.add(cv1)
        cv_store.add(cv2)

        hardware_cvs = cv_store.get_by_category("IT Hardware")
        assert len(hardware_cvs) == 1
        assert hardware_cvs[0].id == "sewp-v"

    def test_get_priority_score(self, cv_store):
        """Test getting priority score."""
        cv = ContractVehicle(id="nasa", name="NASA SOLUTIONS", priority_score=92.0)
        cv_store.add(cv)

        score = cv_store.get_priority_score("NASA SOLUTIONS")
        assert score == 92.0

    def test_get_priority_score_not_found(self, cv_store):
        """Test getting priority score for non-existent CV returns 0."""
        score = cv_store.get_priority_score("Unknown")
        assert score == 0.0


class TestPartnerStore:
    """Tests for Partner entity store."""

    @pytest.fixture
    def partner_store(self, tmp_path):
        """Create temporary Partner store."""
        storage_path = tmp_path / "partners.json"
        return PartnerStore(str(storage_path))

    def test_add_partner(self, partner_store):
        """Test adding a partner."""
        partner = Partner(
            id="partner-1",
            name="TechPartner",
            tier="Platinum",
            oem_affiliations=["microsoft", "cisco"],
        )
        added = partner_store.add(partner)

        assert added.id == "partner-1"
        assert added.tier == "Platinum"

    def test_get_by_oem(self, partner_store):
        """Test getting partners by OEM affiliation."""
        p1 = Partner(id="p1", name="Partner 1", tier="Platinum", oem_affiliations=["microsoft"])
        p2 = Partner(id="p2", name="Partner 2", tier="Gold", oem_affiliations=["microsoft", "cisco"])
        partner_store.add(p1)
        partner_store.add(p2)

        microsoft_partners = partner_store.get_by_oem("microsoft")
        assert len(microsoft_partners) == 2

        cisco_partners = partner_store.get_by_oem("cisco")
        assert len(cisco_partners) == 1


class TestCustomerStore:
    """Tests for Customer entity store."""

    @pytest.fixture
    def customer_store(self, tmp_path):
        """Create temporary Customer store."""
        storage_path = tmp_path / "customers.json"
        return CustomerStore(str(storage_path))

    def test_add_customer(self, customer_store):
        """Test adding a customer."""
        customer = Customer(
            id="customer-1",
            name="CustomerAlpha",
            category="DOD",
            region="East",
            tier="Strategic",
        )
        added = customer_store.add(customer)

        assert added.id == "customer-1"
        assert added.category == "DOD"
        assert added.region == "East"

    def test_get_by_category(self, customer_store):
        """Test getting customers by category."""
        c1 = Customer(id="c1", name="Customer 1", category="DOD", region="East")
        c2 = Customer(id="c2", name="Customer 2", category="DOD", region="West")
        c3 = Customer(id="c3", name="Customer 3", category="Civilian", region="East")
        customer_store.add(c1)
        customer_store.add(c2)
        customer_store.add(c3)

        dod_customers = customer_store.get_by_category("DOD")
        assert len(dod_customers) == 2

    def test_get_by_region(self, customer_store):
        """Test getting customers by region."""
        c1 = Customer(id="c1", name="Customer 1", category="DOD", region="East")
        c2 = Customer(id="c2", name="Customer 2", category="DOD", region="West")
        c3 = Customer(id="c3", name="Customer 3", category="Civilian", region="East")
        customer_store.add(c1)
        customer_store.add(c2)
        customer_store.add(c3)

        east_customers = customer_store.get_by_region("East")
        assert len(east_customers) == 2


class TestDistributorStore:
    """Tests for Distributor entity store."""

    @pytest.fixture
    def distributor_store(self, tmp_path):
        """Create temporary Distributor store."""
        storage_path = tmp_path / "distributors.json"
        return DistributorStore(str(storage_path))

    def test_add_distributor(self, distributor_store):
        """Test adding a distributor."""
        distributor = Distributor(
            id="dist-1",
            name="Tech Distribution",
            tier="Premier",
            oem_authorizations=["microsoft", "cisco"],
            regions_served=["East", "West"],
        )
        added = distributor_store.add(distributor)

        assert added.id == "dist-1"
        assert added.tier == "Premier"

    def test_get_by_oem(self, distributor_store):
        """Test getting distributors by OEM authorization."""
        d1 = Distributor(id="d1", name="Dist 1", tier="Premier", oem_authorizations=["microsoft"])
        d2 = Distributor(id="d2", name="Dist 2", tier="Standard", oem_authorizations=["microsoft", "cisco"])
        distributor_store.add(d1)
        distributor_store.add(d2)

        microsoft_dists = distributor_store.get_by_oem("microsoft")
        assert len(microsoft_dists) == 2

    def test_get_by_region(self, distributor_store):
        """Test getting distributors by region."""
        d1 = Distributor(id="d1", name="Dist 1", tier="Premier", regions_served=["East"])
        d2 = Distributor(id="d2", name="Dist 2", tier="Standard", regions_served=["East", "West"])
        distributor_store.add(d1)
        distributor_store.add(d2)

        east_dists = distributor_store.get_by_region("East")
        assert len(east_dists) == 2


class TestEntityStoreSearch:
    """Tests for search functionality across stores."""

    @pytest.fixture
    def oem_store(self, tmp_path):
        """Create temporary OEM store with test data."""
        storage_path = tmp_path / "oems.json"
        store = OEMStore(str(storage_path))

        store.add(OEM(id="ms", name="Microsoft", tier="Strategic"))
        store.add(OEM(id="cisco", name="Cisco", tier="Strategic"))
        store.add(OEM(id="dell", name="Dell", tier="Gold"))

        return store

    def test_search_by_tier(self, oem_store):
        """Test searching OEMs by tier."""
        strategic = oem_store.search(tier="Strategic")
        assert len(strategic) == 2

        gold = oem_store.search(tier="Gold")
        assert len(gold) == 1

    def test_search_with_active_filter(self, oem_store):
        """Test searching with active status."""
        oem_store.delete("dell")  # Mark inactive

        all_results = oem_store.search(tier="Gold")
        assert len(all_results) == 1

        active_results = oem_store.search(tier="Gold", active=True)
        assert len(active_results) == 0


class TestBackupAndRecovery:
    """Tests for backup functionality."""

    def test_backup_created_on_save(self, tmp_path):
        """Test that backups are created when saving."""
        storage_path = tmp_path / "oems.json"
        store = OEMStore(str(storage_path))

        # Add first OEM
        store.add(OEM(id="ms", name="Microsoft", tier="Strategic"))

        # Add second OEM - should create backup
        store.add(OEM(id="cisco", name="Cisco", tier="Strategic"))

        # Check backup file exists
        backup_files = list(tmp_path.glob("oems.backup*"))
        assert len(backup_files) >= 1

    def test_json_format_valid(self, tmp_path):
        """Test that saved JSON is valid."""
        storage_path = tmp_path / "oems.json"
        store = OEMStore(str(storage_path))

        store.add(OEM(id="ms", name="Microsoft", tier="Strategic"))

        # Verify JSON is valid
        with open(storage_path) as f:
            data = json.load(f)
            assert "entities" in data
            assert len(data["entities"]) == 1
            assert data["entities"][0]["id"] == "ms"
