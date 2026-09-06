package com.vkr.theaterclient.feature

import com.vkr.theaterclient.core.model.ReservationRequest
import com.vkr.theaterclient.core.model.Seat
import com.vkr.theaterclient.core.model.Show
import com.vkr.theaterclient.core.model.Theater
import com.vkr.theaterclient.core.network.AuthTokenStore
import com.vkr.theaterclient.core.network.LoginRequest
import com.vkr.theaterclient.core.network.PublicApi
import com.vkr.theaterclient.core.network.RegisterRequest
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TheaterRepository @Inject constructor(
    private val api: PublicApi,
    private val tokenStore: AuthTokenStore,
) {
    private fun mapError(t: Throwable): Throwable {
        return when (t) {
            is IOException -> IllegalStateException("Нет соединения с сервером. Проверьте API и сеть.")
            is HttpException -> {
                val msg = when (t.code()) {
                    400 -> "Некорректный запрос. Проверьте введенные данные."
                    401 -> "Неверный логин или пароль."
                    409 -> "Место уже занято. Выберите другое."
                    500 -> "Ошибка сервера. Попробуйте позже."
                    else -> "Ошибка API: ${t.code()}"
                }
                IllegalStateException(msg)
            }
            else -> t
        }
    }

    suspend fun register(email: String, phone: String?, password: String) {
        try {
            api.register(RegisterRequest(email, phone, password))
        } catch (t: Throwable) {
            throw mapError(t)
        }
    }

    suspend fun login(email: String, password: String) {
        try {
            val token = api.login(LoginRequest(email, password))
            tokenStore.save(token.accessToken)
        } catch (t: Throwable) {
            throw mapError(t)
        }
    }

    suspend fun hasActiveSession(): Boolean {
        if (tokenStore.get().isNullOrBlank()) return false
        return try {
            api.me()
            true
        } catch (_: Throwable) {
            tokenStore.clear()
            false
        }
    }

    suspend fun theaters(): List<Theater> = try {
        api.theaters()
    } catch (t: Throwable) {
        throw mapError(t)
    }

    suspend fun shows(theaterId: Int, showDate: String?): List<Show> = try {
        api.shows(theaterId = theaterId, showDate = showDate)
    } catch (t: Throwable) {
        throw mapError(t)
    }

    suspend fun seats(showId: Int): List<Seat> = try {
        api.seats(showId)
    } catch (t: Throwable) {
        throw mapError(t)
    }

    suspend fun reserve(showId: Int, seatNumber: String): Seat {
        return try {
            api.reserve(ReservationRequest(showId = showId, seatNumber = seatNumber))
        } catch (t: Throwable) {
            throw mapError(t)
        }
    }

    suspend fun myReservations(): List<Seat> = try {
        api.myReservations()
    } catch (t: Throwable) {
        throw mapError(t)
    }
}
