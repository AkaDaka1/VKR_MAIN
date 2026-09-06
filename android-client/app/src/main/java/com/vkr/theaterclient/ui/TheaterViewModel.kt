package com.vkr.theaterclient.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vkr.theaterclient.core.model.Seat
import com.vkr.theaterclient.core.model.Show
import com.vkr.theaterclient.core.model.Theater
import com.vkr.theaterclient.feature.TheaterRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TheaterUiState(
    val sessionChecked: Boolean = false,
    val authenticated: Boolean = false,
    val loading: Boolean = false,
    val error: String? = null,
    val theaters: List<Theater> = emptyList(),
    val shows: List<Show> = emptyList(),
    val seats: List<Seat> = emptyList(),
    val reservations: List<Seat> = emptyList(),
    val selectedTheaterId: Int? = null,
    val selectedShowId: Int? = null,
    val showDateFilter: String = "",
)

@HiltViewModel
class TheaterViewModel @Inject constructor(
    private val repository: TheaterRepository,
) : ViewModel() {

    private val _state = MutableStateFlow(TheaterUiState())
    val state: StateFlow<TheaterUiState> = _state.asStateFlow()

    fun checkSession() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            val active = repository.hasActiveSession()
            _state.value = _state.value.copy(
                loading = false,
                sessionChecked = true,
                authenticated = active,
            )
            if (active) loadTheaters()
        }
    }

    fun registerAndLogin(email: String, phone: String?, password: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching {
                repository.register(email, phone, password)
                repository.login(email, password)
            }.onSuccess {
                _state.value = _state.value.copy(loading = false, authenticated = true)
                loadTheaters()
            }.onFailure {
                _state.value = _state.value.copy(loading = false, error = it.message ?: "Auth failed")
            }
        }
    }

    fun login(email: String, password: String) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching { repository.login(email, password) }
                .onSuccess {
                    _state.value = _state.value.copy(loading = false, authenticated = true)
                    loadTheaters()
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Login failed")
                }
        }
    }

    fun loadTheaters() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching { repository.theaters() }
                .onSuccess { list ->
                    _state.value = _state.value.copy(loading = false, theaters = list)
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Failed to load theaters")
                }
        }
    }

    fun loadShows(theaterId: Int, showDate: String? = null) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, selectedTheaterId = theaterId, error = null)
            runCatching { repository.shows(theaterId, showDate?.ifBlank { null }) }
                .onSuccess { list ->
                    _state.value = _state.value.copy(loading = false, shows = list)
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Failed to load shows")
                }
        }
    }

    fun setShowDateFilter(value: String) {
        _state.value = _state.value.copy(showDateFilter = value)
    }

    fun loadSeats(showId: Int) {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, selectedShowId = showId, error = null)
            runCatching { repository.seats(showId) }
                .onSuccess { list ->
                    _state.value = _state.value.copy(loading = false, seats = list)
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Failed to load seats")
                }
        }
    }

    fun reserveSeat(seatNumber: String) {
        val showId = _state.value.selectedShowId ?: return
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching { repository.reserve(showId, seatNumber) }
                .onSuccess {
                    _state.value = _state.value.copy(loading = false)
                    loadSeats(showId)
                    loadReservations()
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Failed to reserve seat")
                }
        }
    }

    fun loadReservations() {
        viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            runCatching { repository.myReservations() }
                .onSuccess { list ->
                    _state.value = _state.value.copy(loading = false, reservations = list)
                }
                .onFailure {
                    _state.value = _state.value.copy(loading = false, error = it.message ?: "Failed to load reservations")
                }
        }
    }
}
